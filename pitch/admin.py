from django.contrib import admin, messages
from django.http import HttpResponse
from .models import Voucher, Pitch, Order, Comment, Image, PitchRating,AccessComment
from .models import Pitch
from account.mail import send_mail_custom
from django.utils.translation import gettext
from project1.settings import HOST
from django.urls import reverse_lazy
from datetime import datetime, timedelta
from django.db.models import Q
from pitch.forms import FormCustomSearchAdminSite
from import_export.admin import ExportActionModelAdmin
import xlwt


class ImageInline(admin.TabularInline):
    model = Image


@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    list_display = ("address", "title", "description", "size", "surface", "price")
    fields = [
        ("address"),
        ("title"),
        ("size"),
        ("phone"),
        ("surface"),
        ("price"),
        ("description"),
    ]
    inlines = [ImageInline]
    list_filter = ("size", "surface", "price")

    def has_pending_or_future_orders(self, obj):
        return obj.order_set.filter(status__in=["o"]).exists()

    def delete_model(self, request, obj):
        if obj.has_pending_or_future_orders():
            messages.error(
                request,
                gettext(
                    "Cannot delete this pitch because there are pending or future orders associated with it."
                ),
            )
        else:
            super().delete_model(request, obj)


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ("name", "min_cost", "discount", "count")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "renter",
        "pitch",
        "rating",
        "comment",
        "created_date",
    )
    def delete_queryset(self, request, queryset):

        for comment in queryset:
            print(comment.pitch.id)
            if PitchRating.objects.filter(pitch_id=comment.pitch.id).exists():
                pitch_rating = PitchRating.objects.get(pitch_id=comment.pitch.id)
                pitch_rating.delete_avg_rating(comment.rating)
        queryset.delete()

class PitchRatingAdmin(admin.ModelAdmin):
    list_display = ('pitch', 'avg_rating', 'count_comment')
    readonly_fields = ('avg_rating', 'count_comment')

admin.site.register(PitchRating, PitchRatingAdmin)

class AccessCommentAdmin(admin.ModelAdmin):
    list_display = ('renter', 'pitch', 'count_comment_created')
admin.site.register(AccessComment, AccessCommentAdmin)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    @admin.action(description=gettext("Export as excel"))
    def export_as_excel(self, request, queryset):
        response = HttpResponse(content_type="application/ms-excel")
        name = "OrderList" + datetime.now().strftime("%Y%m%d%H%M%s")
        response["Content-Disposition"] = 'attachment; filename="%s.xls"' % name

        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Sheet1")

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = [
            "id",
            "renter",
            "price",
            "pitch",
            "time_start",
            "time_end",
            "cost",
        ]

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        for row in queryset:
            row_num += 1
            pitch = row.pitch.title + "(%s%s)" % (HOST, row.pitch.get_absolute_url())
            renter = row.renter.username
            for col_num in range(len(columns)):
                if columns[col_num] == "time_start" or columns[col_num] == "time_end":
                    time = getattr(row, columns[col_num])
                    ws.write(
                        row_num, col_num, time.strftime("%Y-%m-%d %H:%M"), font_style
                    )
                elif columns[col_num] == "pitch":
                    ws.write(row_num, col_num, pitch, font_style)
                elif columns[col_num] == "renter":
                    ws.write(row_num, col_num, renter, font_style)
                else:
                    ws.write(
                        row_num, col_num, getattr(row, columns[col_num]), font_style
                    )

        wb.save(response)

        return response

    actions = [export_as_excel]
    list_display = (
        "status",
        "renter",
        "time_start",
        "time_end",
        "cost",
        "created_date",
    )
    list_filter = ("pitch", "pitch__surface", "pitch__size")

    change_list_template = "admin/custom_change_list.html"
    advanced_search_fields = {}
    search_form_data = None
    search_form = FormCustomSearchAdminSite

    def changelist_view(self, request, extra_context=None):
        if hasattr(self, "search_form"):
            self.other_search_fields = {}
            self.search_form_data = self.search_form(request.GET.dict())
            extra_context = {"asf": self.search_form}
            self.extract_advanced_search_terms(request.GET)

        return super().changelist_view(request, extra_context=extra_context)

    def check_input_search(self):
        if (
            self.advanced_search_fields.get("time_start")
            and self.advanced_search_fields.get("time_start")[0]
            and self.advanced_search_fields.get("time_end")
            and self.advanced_search_fields.get("time_end")[0]
        ):
            time_start = datetime.strptime(
                self.advanced_search_fields.get("time_start")[0], "%Y-%m-%d %H:%M:%S"
            )
            time_end = datetime.strptime(
                self.advanced_search_fields.get("time_end")[0], "%Y-%m-%d %H:%M:%S"
            )
            if time_end < time_start + timedelta(hours=1):
                raise ValueError(
                    gettext("Time end must be at least 1 hour longer than start time")
                )

        return True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        query = Q()
        try:
            results = queryset.filter(query)
            self.check_input_search()
            if (
                self.advanced_search_fields.get("time_start")
                and self.advanced_search_fields.get("time_start")[0]
            ):
                results = results.filter(
                    time_start__gte=self.advanced_search_fields.get("time_start")[0],
                )
            if (
                self.advanced_search_fields.get("time_end")
                and self.advanced_search_fields.get("time_end")[0]
            ):
                results = results.filter(
                    time_start__lte=self.advanced_search_fields.get("time_end")[0],
                )
            return results

        except Exception as e:
            messages.add_message(request, messages.ERROR, e)
            return queryset.none()

    def extract_advanced_search_terms(self, request):
        request._mutable = True

        if self.search_form_data is not None:
            for key in self.search_form_data.fields.keys():
                temp = request.pop(key, None)
                if temp:
                    self.advanced_search_fields[key] = temp

        request._mutable = False

    def send_order_notification(request, email, subject, html_template, context):
        try:
            send_mail_custom(subject, [email], html_template, context)
            messages.success(request, "Email sent successfully.")
        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")

    def save_model(self, request, obj, form, change):
        # Check if the order status has changed
        if change and "status" in form.changed_data:
            old_status = form.initial.get("status")
            new_status = form.cleaned_data.get("status")
            email = obj.renter.email
            if old_status == "o" and new_status == "c":
                try:
                    send_mail_custom(
                        gettext("Notice to order a pitch from Pitch App"),
                        [email],
                        None,
                        "email/confirmed_email.html",
                        link=HOST + reverse_lazy("order-detail", kwargs={"pk": obj.id}),
                        username=obj.renter.username,
                        time_start=obj.time_start,
                        time_end=obj.time_end,
                        pitch_title=obj.pitch.title,
                        cost=obj.cost,
                    )
                    messages.success(
                        request, "Confirmation email has been sent successfully."
                    )
                except Exception as e:
                    messages.error(
                        request, f"Failed to send confirmation email: {str(e)}"
                    )

            elif old_status == "o" and new_status == "d":
                # Send cancellation email
                try:
                    send_mail_custom(
                        gettext("Notice to order a pitch from Pitch App"),
                        [email],
                        None,
                        "email/canceled_email.html",
                        link=HOST + reverse_lazy("order-detail", kwargs={"pk": obj.id}),
                        username=obj.renter.username,
                        time_start=obj.time_start,
                        time_end=obj.time_end,
                        pitch_title=obj.pitch.title,
                        cost=obj.cost,
                    )
                    messages.success(
                        request, "Cancellation email has been sent successfully."
                    )
                except Exception as e:
                    messages.error(
                        request, f"Failed to send cancellation email: {str(e)}"
                    )
        super().save_model(request, obj, form, change)
