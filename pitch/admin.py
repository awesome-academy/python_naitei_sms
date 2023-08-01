from django.contrib import admin, messages
from .models import Voucher, Pitch, Order, Comment, Image
from .models import Pitch
from account.mail import send_mail_custom
from django.utils.translation import gettext
from project1.settings import HOST
from django.urls import reverse_lazy

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
        return obj.order_set.filter(status__in=['o']).exists()

    def delete_model(self, request, obj):
        if obj.has_pending_or_future_orders():
            messages.error(request, "Cannot delete this pitch because there are pending or future orders associated with it.")
        else:
            super().delete_model(request, obj)

# Register the Admin classes for Book using the decorator


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

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "status",
        "renter",
        "time_start",
        "time_end",
        "cost",
        "created_date",
    )
    def send_order_notification(request, email, subject, html_template, context):
        try:
            send_mail_custom(subject, [email], html_template, context)
            messages.success(request, "Email sent successfully.")
        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")

    def save_model(self, request, obj, form, change):
        # Check if the order status has changed
        if change and 'status' in form.changed_data:
            old_status = form.initial.get('status')
            new_status = form.cleaned_data.get('status')
            email = obj.renter.email
            if old_status == 'o' and new_status == 'c':
                try:
                    send_mail_custom(
                        gettext("Notice to order a pitch from Pitch App"),
                        email,
                        None,
                        "email/confirmed_email.html",
                        link =  HOST + reverse_lazy("order-detail", kwargs={"pk": obj.id}),
                        username=obj.renter.username,
                        time_start=obj.time_start,
                        time_end=obj.time_end,
                        pitch_title=obj.pitch.title,
                        cost=obj.cost,
                    )
                    messages.success(request, "Confirmation email has been sent successfully.")
                except Exception as e:
                    messages.error(request, f"Failed to send confirmation email: {str(e)}")

            elif old_status == 'o' and new_status == 'd':
                # Send cancellation email
                try:
                    send_mail_custom(
                        gettext("Notice to order a pitch from Pitch App"),
                        email,
                        None,
                        "email/canceled_email.html",
                        link =  HOST + reverse_lazy("order-detail", kwargs={"pk": obj.id}),
                        username=obj.renter.username,
                        time_start=obj.time_start,
                        time_end=obj.time_end,
                        pitch_title=obj.pitch.title,
                        cost=obj.cost,
                    )
                    messages.success(request, "Cancellation email has been sent successfully.")
                except Exception as e:
                    messages.error(request, f"Failed to send cancellation email: {str(e)}")
        super().save_model(request, obj, form, change)
