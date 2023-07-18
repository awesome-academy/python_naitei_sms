from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext
from django.views import generic
from account.mail import send_mail_custom
from pitch.models import Pitch, Order
from django.http import Http404, HttpResponseRedirect
from pitch.forms import RentalPitchModelForm
import datetime
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from pitch.custom_fnc import convert_timedelta
from project1.settings import HOST

from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.
def index(request):
    context = {"title": gettext("Home Page")}
    return render(request, "index.html", context=context)


class PitchListView(generic.ListView):
    model = Pitch
    paginate_by = 10

    def get_queryset(self):
        return Pitch.objects.filter(image__isnull=False)

    def get_context_data(self, **kwargs):
        context = super(PitchListView, self).get_context_data(**kwargs)
        pitches = context["pitch_list"]
        for pitch in pitches:
            if pitch.image.all().exists():
                pitch.banner = pitch.image.all()[0].image.url
            else:
                pitch.banner = "/uploads/uploads/default-image.jpg"
            pitch.surface = pitch.get_label_grass()
            pitch.size = pitch.get_label_size()
        context["pitch_list"] = pitches
        return context


@login_required
def pitch_detail(request, pk):
    context = {}
    try:
        pitch = Pitch.objects.get(pk=pk)
    except Pitch.DoesNotExist:
        raise Http404("Pitch does not exist")
    context["pitch"] = pitch
    start_rental_date = datetime.datetime.now() + datetime.timedelta(days=1)
    context["images"] = context["pitch"].image.all()
    if request.method == "POST":
        form = RentalPitchModelForm(request.POST, pitch=pitch)
        if form.is_valid():
            time_start = form.cleaned_data["time_start"]
            time_end = form.cleaned_data["time_end"]
            voucher = form.cleaned_data["voucher"]
            email = request.user.email
            username = request.user.username
            link = HOST + reverse_lazy("index")

            cost = (
                convert_timedelta(time_end - time_start) * (pitch.price)
                - voucher.discount
            )
            Order.objects.create(
                pitch=pitch,
                time_start=time_start,
                time_end=time_end,
                renter=request.user,
                price=pitch.price,
                cost=cost,
                voucher=voucher,
            )

            send_mail_custom(
                gettext("Notice to order a pitch from Pitch App"),
                email,
                None,
                "email/notify_order_pitch.html",
                link=link,
                username=username,
            )

            return HttpResponseRedirect(reverse_lazy("index"))
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

    return render(request, "pitch/pitch_detail.html", context=context)


class MyOrderedView(LoginRequiredMixin, generic.ListView):
    model = Order
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(renter=self.request.user).order_by("created_date")
