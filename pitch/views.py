import re
import pandas as pd
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils.translation import gettext
from django.views import generic
from account.mail import send_mail_custom
from pitch.models import (
    Pitch,
    Order,
    Comment,
    PitchRating,
    AccessComment,
    Favorite,
    Image,
)
from django.db.models import Count
from pitch.forms import RentalPitchModelForm, CancelOrderModelForm
import datetime
from django.contrib.auth.models import User
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from pitch.custom_fnc import convert_timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from account.mail import send_mail_custom
from django.utils.translation import gettext_lazy as _
from project1.settings import HOST
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from .forms import SearchForm, CommentForm
from django.db import transaction
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError


# Create your views here.
def index(request):
    pitches = (
        Pitch.objects.all()
        .annotate(num_orders=Count("order", filter=Q(order__status="c")))
        .order_by("-num_orders")[:3]
        .prefetch_related("image")
    )
    for pitch in pitches:
        if pitch.image.all().exists():
            pitch.banner = pitch.image.all()[0].image.url
        else:
            pitch.banner = "/media/uploads/default-image.jpg"
        pitch.surface = pitch.get_label_grass()
        pitch.size = pitch.get_label_size()
    context = {"pitch_list": pitches}
    return render(request, "index.html", context=context)


@transaction.atomic
@login_required
def pitch_detail(request, pk):
    context = {}
    try:
        pitch = Pitch.objects.get(pk=pk)
        pitch_rating = PitchRating.objects.get(pitch=pitch)
    except Pitch.DoesNotExist:
        raise Http404("Pitch does not exist")
    except PitchRating.DoesNotExist:
        pitch_rating = PitchRating.objects.create(pitch=pitch)

    user_favorites = Favorite.objects.filter(renter=request.user, pitch=pitch)
    is_favorite = user_favorites.exists()

    context["user_favorites"] = user_favorites
    context["is_favorite"] = is_favorite

    context["pitch"] = pitch

    context["pitch_rating"] = pitch_rating

    start_rental_date = datetime.datetime.now() + datetime.timedelta(days=1)
    context["images"] = context["pitch"].image.all()

    comments = Comment.objects.filter(pitch=pitch)
    context["comments"] = comments

    user_comment_exists = Comment.objects.filter(pitch=pitch, renter=request.user)
    context["user_comment_exists"] = user_comment_exists
    orders = Order.objects.filter(pitch=pitch, status="c", renter=request.user)
    context["orders"] = orders
    try:
        access_comment = AccessComment.objects.get(renter=request.user, pitch=pitch)
    except:
        access_comment = AccessComment.objects.create(renter=request.user, pitch=pitch)
    context["access_comment"] = access_comment

    form = RentalPitchModelForm(request.POST, pitch=pitch)
    context["form"] = RentalPitchModelForm(
        initial={
            "time_start": start_rental_date,
            "time_end": start_rental_date + datetime.timedelta(hours=1),
        },
        pitch=pitch,
    )
    if request.method == "POST" and request.GET.get("action") == "addcomment":
        comment_form = CommentForm(request.POST)
        if (
            comment_form.is_valid()
            and orders.exists()
            and access_comment.count_comment_created > 0
        ):
            data = Comment()
            data.comment = comment_form.cleaned_data["comment"]
            data.rating = comment_form.cleaned_data["rating"]
            data.ip = request.META.get("REMOTE_ADDR")
            data.pitch_id = pk
            data.renter = request.user
            data.save()
            pitch_rating.create_avg_rating(data.rating)
            access_comment.counting_left()
            return HttpResponseRedirect(pitch.get_absolute_url())
        else:
            context["comment_form"] = comment_form
    elif request.method == "POST" and request.GET.get("action") == "edit_comment":
        comment_id = request.GET.get("comment_id")
        comment = Comment.objects.get(pitch=pitch, id=comment_id)
        comment_form = CommentForm(request.POST, instance=comment)
        if comment_form.is_valid():
            pitch_rating.update_avg_rating(
                comment_form.cleaned_data["rating"] - comment.rating
            )
            data = comment_form.save(commit=False)
            data.save()
            return HttpResponseRedirect(pitch.get_absolute_url())
        else:
            context["edit_comment_form"] = comment_form

    elif request.method == "POST":
        if form.is_valid():
            time_start = form.cleaned_data["time_start"]
            time_end = form.cleaned_data["time_end"]
            voucher = form.cleaned_data["voucher"]
            email = request.user.email
            username = request.user.username

            cost = convert_timedelta(time_end - time_start) * (pitch.price)
            if voucher:
                cost -= voucher.discount

            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        pitch=pitch,
                        time_start=time_start,
                        time_end=time_end,
                        renter=request.user,
                        price=pitch.price,
                        cost=cost,
                        voucher=voucher,
                    )
                    access_comment.counting_created()
                    link = HOST + reverse_lazy("order-detail", kwargs={"pk": order.id})

                    send_mail_custom(
                        gettext("Notice to order a pitch from Pitch App"),
                        [email],
                        None,
                        "email/notify_order_pitch.html",
                        link=link,
                        username=username,
                        time_start=time_start,
                        time_end=time_end,
                        pitch_title=pitch.title,
                        price=pitch.price,
                        cost=cost,
                    )

                    return HttpResponseRedirect(
                        reverse_lazy("order-detail", kwargs={"pk": order.id})
                    )
            except Exception:
                return HttpResponse(_("Something went wrong, please come back."))

        else:
            context["form"] = form
    else:
        context["form"] = RentalPitchModelForm(
            initial={
                "time_start": start_rental_date,
                "time_end": start_rental_date + datetime.timedelta(hours=1),
            },
            pitch=pitch,
        )
        context["comment_form"] = CommentForm

    paginator = Paginator(comments, 2)
    is_pagination = True if paginator.num_pages >= 2 else False
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["page_obj"] = page_obj
    context["is_paginated"] = is_pagination

    return render(request, "pitch/pitch_detail.html", context=context)


class MyOrderedView(LoginRequiredMixin, generic.ListView):
    model = Order
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(renter=self.request.user).order_by("created_date")


@login_required
def order_cancel(request, pk):
    context = {}
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        raise Http404("Order does not exist")
    context["order"] = order

    if request.method == "POST":
        form = CancelOrderModelForm(request.POST)
        if form.is_valid():
            admins = User.objects.filter(is_superuser=1)
            emails = list(map(lambda x: x.email, admins))
            username = request.user.username
            link = HOST + "/admin/pitch/order/%d/change/" % pk
            order.status = "d"
            try:
                with transaction.atomic():
                    order.save()
                    send_mail_custom(
                        _("Notice of customer order cancellation from Pitch App"),
                        emails,
                        None,
                        "email/notify_cancel_order.html",
                        link=link,
                        username=username,
                        time_start=order.time_start,
                        time_end=order.time_end,
                        pitch_title=order.pitch.title,
                        cost=order.cost,
                    )
            except Exception:
                return HttpResponse(_("Something went wrong, please come back."))
        else:
            context["form"] = form
    else:
        if order.renter.id != request.user.id:
            return render(
                request,
                "error.html",
                {"text_content": _("You can not access this page.")},
                status=302,
            )
        if order.status == "o":
            context["form"] = CancelOrderModelForm(
                initial={
                    "status": "o",
                },
            )

    return render(request, "pitch/order_detail.html", context=context)


def search_view(request):
    form = SearchForm(request.GET)
    query = request.GET.get("q")
    address = request.GET.get("address")
    price = request.GET.get("price")
    size = request.GET.get("size")
    surface = request.GET.get("surface")
    results = []
    ask = [query, address, price, size, surface]
    queryFilter = ""
    if surface:
        queryFilter += "surface = '%s'" % surface
    if size:
        if queryFilter != "":
            queryFilter += " and "
        queryFilter += "size = '%s'" % size
    if price:
        if queryFilter != "":
            queryFilter += " and "
        queryFilter += " price <= %s" % price
    if address:
        if queryFilter != "":
            queryFilter += " and "
        queryFilter += "address = '%s'" % address
    if query:
        if queryFilter != "":
            queryFilter += " and "
        queryFilter += "MATCH(title,description) AGAINST('%s') > 0.01 " % query

    if len(queryFilter) > 0:
        queryFilter = "SELECT * FROM pitches WHERE " + queryFilter
    else:
        queryFilter = "SELECT * FROM pitches "

    results = Pitch.objects.raw(queryFilter).prefetch_related("image")

    for pitch in results:
        if pitch.image.all().exists():
            pitch.banner = pitch.image.all()[0].image.url
        else:
            pitch.banner = "/media/uploads/default-image.jpg"
        pitch.surface = pitch.get_label_grass()
        pitch.size = pitch.get_label_size()
    paginator = Paginator(results, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "query": ask,
        "form": form,
        "page_obj": page_obj,
        "is_paginated": True,
    }

    return render(request, "pitch/pitch_search.html", context)


@staff_member_required
def upload_pitch_data(request):
    if request.method == "POST":
        excel_file = request.FILES["excel_file"]
        if excel_file.name.endswith(".xlsx"):
            try:
                df_pitch_data = pd.read_excel(excel_file, sheet_name="PitchData")
            except Exception as e:
                messages.error(request, f"Error reading sheets: {str(e)}")
                return HttpResponseRedirect(request.path_info)

            success_count_data = 0
            failure_count_data = 0
            success_count_images = 0
            failure_count_images = 0
            error_details_data = []
            error_details_images = []
            for index, row in df_pitch_data.iterrows():
                try:
                    required_fields = ["title", "address", "size", "surface", "price"]
                    missing_fields = [
                        field
                        for field in required_fields
                        if pd.isnull(row[field]) or row[field] == ""
                    ]
                    if missing_fields:
                        failure_count_data += 1
                        error_details_data.append(
                            f"Error at row {index + 2}: Required fields cannot be empty: {', '.join(missing_fields)}"
                        )
                    else:
                        pitch = Pitch(
                            title=row["title"],
                            description=row["description"],
                            price=row["price"],
                            address=row["address"],
                            phone=row["phone"],
                            size=row["size"],
                            surface=row["surface"],
                        )
                        try:
                            pitch.full_clean()
                            pitch.save()
                            for i in range(1, 4):
                                image_url = row[f"image{i}"]
                                if image_url and isinstance(image_url, str):
                                    try:
                                        image = Image(image=image_url, pitch=pitch)
                                        image.full_clean()
                                        image.save()
                                        success_count_images += 1
                                    except ValidationError as e:
                                        failure_count_images += 1
                                        field_errors = []
                                        for field, errors in e.message_dict.items():
                                            field_errors.append(
                                                f"{field.capitalize()}: {', '.join(errors)}"
                                            )
                                        error_details_images.append(
                                            f"Error at row {index + 2}, image{i}: {'; '.join(field_errors)}"
                                        )
                            success_count_data += 1
                        except ValidationError as e:
                            failure_count_data += 1
                            field_errors = []
                            for field, errors in e.message_dict.items():
                                field_errors.append(
                                    f"{field.capitalize()}: {', '.join(errors)}"
                                )

                            error_details_data.append(
                                f"Error at row {index + 2}: {'; '.join(field_errors)}"
                            )
                except Exception as e:
                    failure_count_data += 1
                    error_details_data.append(f"Error at row {index + 2}: {str(e)}")

            if failure_count_data > 0:
                for error_detail in error_details_data:
                    messages.error(request, f"PitchData import: {error_detail}")

            if failure_count_images > 0:
                for error_detail in error_details_images:
                    messages.error(request, f"PitchImages import: {error_detail}")

            messages.success(
                request,
                f"PitchData import successful: {success_count_data} records added.",
            )
            messages.success(
                request,
                f"PitchImages import successful: {success_count_images} records added.",
            )
            messages.error(
                request, f"Import failed (PitchData): {failure_count_data} records."
            )
            messages.error(
                request, f"Import failed (PitchImages): {failure_count_images} records."
            )

            return HttpResponseRedirect(request.path_info)
        else:
            messages.error(request, "Please upload a valid Excel file.")
            return HttpResponseRedirect(request.path_info)

    return render(request, "admin/upload_pitch_data.html")


@login_required
def toggle_favorite(request, pk):
    try:
        pitch = Pitch.objects.get(pk=pk)
    except Pitch.DoesNotExist:
        pass
    try:
        favorite = Favorite.objects.get(renter=request.user, pitch=pitch)
        favorite.delete()
    except Favorite.DoesNotExist:
        favorite = Favorite.objects.create(renter=request.user, pitch=pitch)

    return redirect("pitch-detail", pk=pk)


def favorite_pitches(request):
    favorite_pitches = Favorite.objects.filter(renter=request.user).select_related(
        "pitch"
    )

    for favorite in favorite_pitches:
        pitch = favorite.pitch
        if pitch.image.all().exists():
            pitch.banner = pitch.image.all()[0].image.url
        else:
            pitch.banner = "/media/uploads/default-image.jpg"
        pitch.surface = pitch.get_label_grass()
        pitch.size = pitch.get_label_size()
    paginator = Paginator(favorite_pitches, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "is_paginated": True,
        "favorite_pitches": favorite_pitches,
    }
    return render(request, "pitch/favorite_list.html", context=context)
