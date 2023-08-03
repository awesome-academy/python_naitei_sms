import datetime

from django.test import TestCase
from django.utils import timezone
from pitch.factory import PitchFactory, UserFactory, OrderFactory, VoucherFactory
import datetime
from pitch.forms import RentalPitchModelForm, CancelOrderModelForm
from account.forms import RegisterForm


class RentalPitchFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.voucher = VoucherFactory()
        cls.pitch = PitchFactory()

    def test_rental_pitch_label(self):
        form = RentalPitchModelForm(pitch=self.pitch)
        self.assertTrue(form.fields["time_start"].label == "Start time ")
        self.assertTrue(form.fields["time_end"].label == "Return time ")
        self.assertTrue(form.fields["voucher"].label == "Voucher")

    def test_rental_pitch_field_help_text(self):
        form = RentalPitchModelForm(pitch=self.pitch)
        self.assertEqual(
            form.fields["time_start"].help_text,
            "Enter the current time big time.",
        )
        self.assertEqual(
            form.fields["time_end"].help_text,
            "Enter a minimum time greater than 1 hour start.",
        )

    def test_rental_pitch_is_valid(self):
        start = timezone.now() + datetime.timedelta(hours=4)
        end = start + datetime.timedelta(hours=3)
        form = RentalPitchModelForm(
            data={"time_start": start, "time_end": end, "voucher": self.voucher},
            pitch=self.pitch,
        )
        self.assertTrue(form.is_valid())

    def test_time_start_is_invalid(self):
        start = timezone.now() - datetime.timedelta(hours=4)
        end = start + datetime.timedelta(hours=1)
        form = RentalPitchModelForm(
            data={"time_start": start, "time_end": end}, pitch=self.pitch
        )
        self.assertFalse(form.is_valid())

    def test_time_end_is_invalid(self):
        start = timezone.now() + datetime.timedelta(hours=1)
        end = start + datetime.timedelta(minutes=1)
        form = RentalPitchModelForm(
            data={"time_start": start, "time_end": end}, pitch=self.pitch
        )
        self.assertFalse(form.is_valid())

    def test_order_is_exists(self):
        start = timezone.now() + datetime.timedelta(hours=4)
        end = start + datetime.timedelta(hours=1)
        OrderFactory(
            renter=self.user,
            pitch=self.pitch,
            time_start=start,
        )
        form = RentalPitchModelForm(
            data={"time_start": start, "time_end": end}, pitch=self.pitch
        )
        self.assertFalse(form.is_valid())

    def test_order_is_exists(self):
        start = timezone.now() + datetime.timedelta(hours=4)
        end = start + datetime.timedelta(hours=1)
        OrderFactory(
            renter=self.user,
            pitch=self.pitch,
            time_start=start,
        )
        form = RentalPitchModelForm(
            data={"time_start": start, "time_end": end}, pitch=self.pitch
        )
        self.assertFalse(form.is_valid())

    def test_order_is_exists(self):
        start = timezone.now() + datetime.timedelta(hours=4)
        end = start + datetime.timedelta(hours=1)
        OrderFactory(
            renter=self.user,
            pitch=self.pitch,
            time_start=start,
        )
        form = RentalPitchModelForm(
            data={"time_start": start, "time_end": end}, pitch=self.pitch
        )
        self.assertFalse(form.is_valid())

    def test_voucher_is_invalid(self):
        start = timezone.now() + datetime.timedelta(hours=1)
        end = start + datetime.timedelta(hours=1)
        form = RentalPitchModelForm(
            data={"time_start": start, "time_end": end, "voucher": self.voucher},
            pitch=self.pitch,
        )
        self.assertFalse(form.is_valid())


class CancelOrderFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.voucher = VoucherFactory()
        cls.pitch = PitchFactory()

    def test_cancel_order_is_valid(self):
        form = CancelOrderModelForm(
            data={"status": "o"},
        )
        self.assertTrue(form.is_valid())

    def test_cancel_order_is_invalid(self):
        form = CancelOrderModelForm(
            data={"status": "c"},
        )
        self.assertFalse(form.is_valid())


class RegisterFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_register_is_valid(self):
        username = "user"
        email = "user@gmail.com"
        password1 = "admin@123"
        password2 = "admin@123"
        form = RegisterForm(
            data={
                "username": username,
                "email": email,
                "password1": password1,
                "password2": password2,
            },
        )
        self.assertTrue(form.is_valid())

    def test_username_is_invalid(self):
        username = "user1"
        email = "user@gmail.com"
        password1 = "admin@123"
        password2 = "admin@123"
        form = RegisterForm(
            data={
                "username": username,
                "email": email,
                "password1": password1,
                "password2": password2,
            },
        )
        self.assertFalse(form.is_valid())

    def test_password_is_invalid(self):
        username = "user"
        email = "user@gmail.com"
        password1 = "admin@1234"
        password2 = "admin@123"
        form = RegisterForm(
            data={
                "username": username,
                "email": email,
                "password1": password1,
                "password2": password2,
            },
        )
        self.assertFalse(form.is_valid())

    def test_email_is_exist(self):
        username = "user"
        email = "user1W@gmail.com"
        password1 = "admin@1234"
        password2 = "admin@123"
        form = RegisterForm(
            data={
                "username": username,
                "email": email,
                "password1": password1,
                "password2": password2,
            },
        )
        self.assertFalse(form.is_valid())
