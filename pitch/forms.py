from django.forms import ModelForm, DateTimeField, Form
from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django.core.exceptions import ValidationError
from pitch.models import Order, Comment
from datetime import timedelta
from django.utils import timezone
from pitch.custom_fnc import convert_timedelta
from django.utils.translation import gettext as _
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class RentalPitchModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.pitch = kwargs.pop("pitch")
        super(RentalPitchModelForm, self).__init__(*args, **kwargs)

    def clean_time_start(self):
        data = self.cleaned_data["time_start"]

        if data <= timezone.now():
            raise ValidationError(_("Start time must be greater than current time."))
        return data

    def clean_time_end(self):
        pitch = self.pitch
        try:
            start = self.cleaned_data["time_start"]
        except KeyError:
            raise ValidationError(_("Invalid time start values."))
        end = self.cleaned_data["time_end"]
        ordered = (
            Order.objects.filter(pitch=pitch, time_start__lt=end, time_end__gte=end)
            | Order.objects.filter(
                pitch=pitch, time_start__lte=start, time_end__gt=start
            )
            | Order.objects.filter(
                pitch=pitch, time_start__gte=start, time_end__lte=end
            )
        )

        if ordered.exists():
            raise ValidationError(
                _("This time someone ordered! Please choose another time.")
            )

        if end < start + timedelta(hours=1):
            raise ValidationError(_("Choose a larger time starting at least 1 hour."))

        return end

    def clean_voucher(self):
        voucher = self.cleaned_data["voucher"]
        pitch = self.pitch
        try:
            start = self.cleaned_data["time_start"]
            end = self.cleaned_data["time_end"]
            cost = convert_timedelta(end - start) * (pitch.price)
        except KeyError:
            raise ValidationError(_("Invalid time start and time end values."))

        if voucher and cost < voucher.min_cost:
            raise ValidationError(
                _("The minimum amount has not been reached to apply the voucher.")
            )

        return voucher

    class Meta:
        model = Order
        fields = ["time_start", "time_end", "voucher"]
        labels = {
            "time_start": "Start time ",
            "time_end": "Return time ",
        }
        help_texts = {
            "time_start": "Enter the current time big time.",
            "time_end": "Enter a minimum time greater than 1 hour start.",
        }
        widgets = {
            "time_start": DateTimePickerInput(),
            "time_end": DateTimePickerInput(),
        }


class CancelOrderModelForm(ModelForm):
    def clean_status(self):
        status = self.cleaned_data["status"]

        if status != "o":
            raise ValidationError(
                _("Once the order has been confirmed, it cannot be cancelled.")
            )

        return status

    class Meta:
        model = Order
        fields = ["status"]


SURFACE_CHOICES = [
    ("", _("Surface")),
    ("a", _("Artificial")),
    ("n", _("Natural")),
    ("m", _("Mixed")),
]

SIZE_CHOICES = [
    ("", _("Size")),
    ("1", _("Pitch 5")),
    ("2", _("Pitch 7")),
    ("3", _("Pitch 12")),
]


class SearchForm(forms.Form):
    q = forms.CharField(
        label=_("Key Word"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Search pitch")}
        ),
    )
    surface = forms.ChoiceField(
        label=_("Surface"),
        choices=SURFACE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "onchange": "submitForm()"}),
    )
    size = forms.ChoiceField(
        label=_("Size"),
        choices=SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "onchange": "submitForm()"}),
    )
    address = forms.CharField(
        label=_("Address"),
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Enter address")}
        ),
    )
    price = forms.DecimalField(
        label=_("Price"),
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Enter price")}
        ),
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["comment", "rating"]
        labels = {
            "comment": "Comment",
            "rating": "Rating",
        }

    def clean_comment(self):
        comment = self.cleaned_data["comment"]
        if not comment:
            raise ValidationError("Comment field cannot be empty.")
        return comment

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if not rating:
            raise ValidationError("Please select a rating.")
        return rating


class FormCustomSearchAdminSite(Form):
    time_start = DateTimeField(required=False, widget=DateTimePickerInput())
    time_end = DateTimeField(required=False, widget=DateTimePickerInput())
