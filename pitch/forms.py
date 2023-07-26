from django.forms import ModelForm
from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django.core.exceptions import ValidationError
from pitch.models import Order
from datetime import timedelta
from django.utils import timezone
from pitch.custom_fnc import convert_timedelta


class RentalPitchModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.pitch = kwargs.pop("pitch")
        super(RentalPitchModelForm, self).__init__(*args, **kwargs)

    def clean_time_start(self):
        data = self.cleaned_data["time_start"]
        if data <= timezone.now():
            raise ValidationError("Thời gian bắt đầu phải lớn hơn giờ hiện tại")
        return data

    def clean_time_end(self):
        pitch = self.pitch
        start = self.cleaned_data["time_start"]
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
            raise ValidationError("Đã tồn tại.")

        if end < start + timedelta(hours=1):
            raise ValidationError("Chọn thời gian lớn hơn bắt đầu tối thiếu 1 tiếng.")

        return end

    def clean_voucher(self):
        pitch = self.pitch
        voucher = self.cleaned_data["voucher"]
        start = self.cleaned_data["time_start"]
        end = self.cleaned_data["time_end"]
        cost = convert_timedelta(end - start) * (pitch.price)
        if cost < voucher.min_cost:
            raise ValidationError("Chưa đạt mức tối thiểu để áp dụng voucher.")

        return voucher

    class Meta:
        model = Order
        fields = ["time_start", "time_end", "voucher"]
        labels = {"time_start": "Thời gian bắt đầu: ", "time_end": "Thời gian trả sân:"}
        help_texts = {
            "time_start": "Nhập thời gian lớn hơn hôm nay.",
            "time_end": "Nhập thời gian tối thiểu lớn hơn bắt đầu 1 tiếng.",
        }
        widgets = {
            "time_start": DateTimePickerInput(),
            "time_end": DateTimePickerInput(),
        }
