from django.test import TestCase
from pitch.models import Pitch, Order
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse_lazy, reverse
from pitch.factory import PitchFactory, UserFactory, OrderFactory
from django.utils import timezone
import datetime


class HomeViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PitchFactory()

    def test_redirect(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base_generic.html")

    def test_number_pitch_is_three(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.context["pitch_list"]), 3)


class SearchViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pitches = [
            PitchFactory(size="3") if x < 10 else PitchFactory(surface="m")
            for x in range(0, 20)
        ]

    def test_redirect(self):
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pitch/pitch_search.html")

    def test_number_pitch(self):
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["results"]), 20)

    def test_search_by_size(self):
        response = self.client.get(reverse("search"), QUERY_STRING="size=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["results"]), 10)

    def test_search_by_surface(self):
        response = self.client.get(reverse("search"), QUERY_STRING="surface=m")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["results"]), 10)

    def test_search_by_desc(self):
        response = self.client.get(
            reverse("search"), QUERY_STRING="q=%s" % self.pitches[0].title
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.context["results"]), 1)

    def test_search_by_size_and_surface(self):
        response = self.client.get(reverse("search"), QUERY_STRING="surface=m&size=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["results"]), 0)


class DetailPitchViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pitches = [
            PitchFactory(size="3") if x < 10 else PitchFactory(surface="m")
            for x in range(0, 20)
        ]

        cls.user = UserFactory()
        cls.client = Client()

    def test_not_login(self):
        response = self.client.get(
            reverse("pitch-detail", kwargs={"pk": self.pitches[0].id})
        )
        self.assertEqual(response.status_code, 302)

    def test_login_redirect(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(
            reverse("pitch-detail", kwargs={"pk": self.pitches[0].id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pitch/pitch_detail.html")


class ListMyOrderViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pitch = PitchFactory(size="3")
        cls.user = UserFactory()
        cls.orders = [
            OrderFactory(
                renter=cls.user,
                pitch=cls.pitch,
                time_start=timezone.now() + datetime.timedelta(hours=i + 4),
            )
            for i in range(0, 20)
        ]

        cls.client = Client()

    def test_not_login(self):
        response = self.client.get(reverse("my-ordered"))
        self.assertEqual(response.status_code, 302)

    def test_login_redirect(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(reverse("my-ordered"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pitch/order_list.html")

    def test_pagination_is_true(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(reverse("my-ordered"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"] == True)
        self.assertEqual(len(response.context["order_list"]), 10)


class DetailOrderViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pitch = PitchFactory(size="3")
        cls.user = UserFactory()
        cls.orders = [
            OrderFactory(
                renter=cls.user,
                pitch=cls.pitch,
                time_start=timezone.now() + datetime.timedelta(hours=i + 4),
            )
            for i in range(0, 20)
        ]

        cls.client = Client()

    def test_not_login(self):
        response = self.client.get(
            reverse("order-detail", kwargs={"pk": self.orders[0].id})
        )
        self.assertEqual(response.status_code, 302)

    def test_user_not_order_login(self):
        otherUser = UserFactory()
        self.client.login(username=otherUser.username, password="admin@123")
        response = self.client.get(
            reverse("order-detail", kwargs={"pk": self.orders[0].id})
        )
        self.assertEqual(response.status_code, 302)

    def test_login_redirect(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(
            reverse("order-detail", kwargs={"pk": self.orders[0].id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pitch/order_detail.html")

    def test_price_order(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(
            reverse("order-detail", kwargs={"pk": self.orders[0].id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["order"].pitch.price, self.pitch.price)
