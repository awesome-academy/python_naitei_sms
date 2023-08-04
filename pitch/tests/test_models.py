import os
from django.test import TestCase
from django.conf import settings
from pitch.models import Order, Comment, Voucher, Pitch, Image
from django.contrib.auth.models import User

class VoucherModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.voucher = Voucher.objects.create(
            name="Test Voucher",
            min_cost=1000,
            discount=500,
            count=10
        )

    def test_attribute(self):
        field_label_name = self.voucher._meta.get_field("name").verbose_name
        field_label_min_cost = self.voucher._meta.get_field("min_cost").verbose_name
        field_label_discount = self.voucher._meta.get_field("discount").verbose_name
        field_label_count = self.voucher._meta.get_field("count").verbose_name

        max_length_name = self.voucher._meta.get_field("name").max_length

        self.assertEqual(field_label_name, "name")
        self.assertEqual(field_label_min_cost, "min cost")
        self.assertEqual(field_label_discount, "discount")
        self.assertEqual(field_label_count, "count")

        self.assertEqual(max_length_name, 200)

        self.assertIsNotNone(self.voucher.name)

    def test_object_name(self):
        self.assertEqual(str(self.voucher), self.voucher.name)


class PitchModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pitch = Pitch.objects.create(
            address="Test Address",
            title="Test Pitch",
            description="Test Description",
            phone="1234567890",
            avg_rating=4.5,
            size="1",
            surface="n",
            price=1000
        )

    def test_attribute(self):
        field_label_address = self.pitch._meta.get_field("address").verbose_name
        field_label_title = self.pitch._meta.get_field("title").verbose_name
        field_label_description = self.pitch._meta.get_field("description").verbose_name
        field_label_phone = self.pitch._meta.get_field("phone").verbose_name
        field_label_avg_rating = self.pitch._meta.get_field("avg_rating").verbose_name
        field_label_size = self.pitch._meta.get_field("size").verbose_name
        field_label_surface = self.pitch._meta.get_field("surface").verbose_name
        field_label_price = self.pitch._meta.get_field("price").verbose_name

        max_length_address = self.pitch._meta.get_field("address").max_length
        max_length_title = self.pitch._meta.get_field("title").max_length
        max_length_phone = self.pitch._meta.get_field("phone").max_length

        self.assertEqual(field_label_address, "address")
        self.assertEqual(field_label_title, "title")
        self.assertEqual(field_label_description, "description")
        self.assertEqual(field_label_phone, "phone")
        self.assertEqual(field_label_avg_rating, "avg rating")
        self.assertEqual(field_label_size, "size")
        self.assertEqual(field_label_surface, "surface")
        self.assertEqual(field_label_price, "price")

        self.assertEqual(max_length_address, 200)
        self.assertEqual(max_length_title, 200)
        self.assertEqual(max_length_phone, 100)

        self.assertIsNotNone(self.pitch.title)

    def test_object_name(self):
        self.assertEqual(str(self.pitch), self.pitch.title)

class OrderModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.voucher = Voucher.objects.create(
            name="Test Voucher",
            min_cost=1000,
            discount=500,
            count=10
        )
        cls.pitch = Pitch.objects.create(
            address="Test Address",
            title="Test Pitch",
            description="Test Description",
            phone="1234567890",
            avg_rating=4.5,
            size="1",
            surface="n",
            price=1000
        )
        cls.renter = User.objects.create_user(username="testuser", password="testpassword")
        cls.order = Order.objects.create(
            time_start="2023-07-20 10:00:00",
            time_end="2023-07-20 12:00:00",
            status="n",
            price=1000,
            renter=cls.renter,
            voucher=cls.voucher,
            cost=5000,
            pitch=cls.pitch
        )

    def test_attribute(self):
        field_label_time_start = self.order._meta.get_field("time_start").verbose_name
        field_label_time_end = self.order._meta.get_field("time_end").verbose_name
        field_label_status = self.order._meta.get_field("status").verbose_name
        field_label_price = self.order._meta.get_field("price").verbose_name
        field_label_renter = self.order._meta.get_field("renter").verbose_name
        field_label_voucher = self.order._meta.get_field("voucher").verbose_name
        field_label_cost = self.order._meta.get_field("cost").verbose_name

        self.assertEqual(field_label_time_start, "time start")
        self.assertEqual(field_label_time_end, "time end")
        self.assertEqual(field_label_status, "status")
        self.assertEqual(field_label_price, "price")
        self.assertEqual(field_label_renter, "renter")
        self.assertEqual(field_label_voucher, "voucher")
        self.assertEqual(field_label_cost, "cost")

        self.assertIsNotNone(self.order.time_start)

    def test_object_name(self):
        expected_object_name = f"Order {self.order.pk} - {self.order.renter.username}"
        self.assertEqual(str(self.order), expected_object_name)


class CommentModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pitch = Pitch.objects.create(
            address="Test Address",
            title="Test Pitch",
            description="Test Description",
            phone="1234567890",
            avg_rating=4.5,
            size="1",
            surface="n",
            price=1000
        )
        cls.renter = User.objects.create_user(username="testuser", password="testpassword")
        cls.comment = Comment.objects.create(
            renter=cls.renter,
            pitch=cls.pitch,
            rating=4,
            comment="Test Comment"
        )

    def test_attribute(self):
        field_label_renter = self.comment._meta.get_field("renter").verbose_name
        field_label_pitch = self.comment._meta.get_field("pitch").verbose_name
        field_label_rating = self.comment._meta.get_field("rating").verbose_name
        field_label_comment = self.comment._meta.get_field("comment").verbose_name

        self.assertEqual(field_label_renter, "renter")
        self.assertEqual(field_label_pitch, "pitch")
        self.assertEqual(field_label_rating, "rating")
        self.assertEqual(field_label_comment, "comment")

        self.assertIsNotNone(self.comment.comment)

    def __str__(self):
        return f"Order {self.pk} - {self.renter.username}"

class ImageModelTestCase(TestCase):
    def setUp(self):
        self.pitch = Pitch.objects.create(
            address="Address 1",
            title="Pitch 1",
            description="Description of pitch 1",
            phone="123456789",
            avg_rating=4.5,
            size="1",
            surface="n",
            price=200000,
        )
        self.image = Image.objects.create(pitch=self.pitch)

    def test_image_default(self):
        default_image_path = "/media/default-image.jpg"
        self.assertEqual(self.image.image.url, default_image_path)

    def test_image_upload_to(self):
        expected_path = os.path.join(settings.MEDIA_ROOT, "default-image.jpg")
        self.assertEqual(self.image.image.path, expected_path)
