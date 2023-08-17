import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from pitch.custom_fnc import convert_timedelta
from pitch.models import Pitch, Order, Voucher, Comment
from django.utils import timezone
import datetime


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence("user{}".format)
    email = factory.Sequence("user{}@company.com".format)
    password = factory.PostGenerationMethodCall("set_password", "admin@123")
    is_superuser = False
    is_staff = True
    is_active = True


class PitchFactory(DjangoModelFactory):
    class Meta:
        model = Pitch

    address = factory.Faker("address")
    title = factory.Faker("name")
    description = factory.Faker("sentence", nb_words=40)
    phone = factory.Faker("phone_number")
    price = 1000000


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    time_start = timezone.now() + datetime.timedelta(days=1)

    time_end = factory.LazyAttribute(
        lambda o: o.time_start + datetime.timedelta(hours=1)
    )
    price = factory.LazyAttribute(lambda o: o.pitch.price)
    cost = factory.LazyAttribute(
        lambda o: o.pitch.price * convert_timedelta(o.time_end - o.time_start)
    )


class VoucherFactory(DjangoModelFactory):
    class Meta:
        model = Voucher

    name = factory.Faker("name")
    min_cost = 2000000
    discount = 100000
    count = 100


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    renter = factory.SubFactory(UserFactory)
    pitch = factory.SubFactory(PitchFactory)
    rating = factory.Faker("pyint", min_value=1, max_value=5)
    comment = factory.Faker("sentence", nb_words=20)
