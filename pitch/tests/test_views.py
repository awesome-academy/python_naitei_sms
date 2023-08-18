from django.test import TestCase
from django.test import Client
from django.urls import reverse
from pitch.factory import PitchFactory, UserFactory, OrderFactory
from django.utils import timezone
import datetime
from django.core import mail
from django.contrib.auth.models import User
from account.models import EmailVerify
import uuid
from pitch.models import Order, Comment, AccessComment
from django.db import connections


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
        cursor = connections["default"].cursor()
        cursor.execute("ALTER TABLE pitches ADD FULLTEXT(title, description)")
        cursor.close()

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
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_search_by_size(self):
        response = self.client.get(reverse("search"), QUERY_STRING="size=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_search_by_surface(self):
        response = self.client.get(reverse("search"), QUERY_STRING="surface=m")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_search_by_desc(self):
        response = self.client.get(
            reverse("search"), QUERY_STRING="q=%s" % self.pitches[0].title
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.context["page_obj"]), 1)

    def test_search_by_size_and_surface(self):
        response = self.client.get(reverse("search"), QUERY_STRING="surface=m&size=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 0)


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

    def test_order_pitch(self):
        self.client.login(username=self.user.username, password="admin@123")
        start = timezone.now() + datetime.timedelta(hours=40)
        end = start + datetime.timedelta(hours=1)
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitches[0].id}),
            data={"time_start": start, "time_end": end},
        )
        self.assertEqual(response.status_code, 302)

        order = Order.objects.filter(
            renter=self.user, pitch=self.pitches[0], time_start=start
        )
        self.assertTrue(order.exists())
        self.assertEqual(order[0].status, "o")
        self.assertEqual(len(mail.outbox), 1)


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
        cls.user = UserFactory(is_superuser=True)
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

    def test_cancel_order_pitch(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("order-detail", kwargs={"pk": self.orders[0].id}),
            data={"status": "o"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Order.objects.get(pk=self.orders[0].id).status, "d")


class RegisterViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.client = Client()

    def test_logged_in(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(reverse("signup"))
        self.assertRedirects(
            response,
            "/pitch/",
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_not_login(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)

    def test_send_email(self):
        username = "user"
        email = "user@gmail.com"
        password1 = "admin@123"
        password2 = "admin@123"
        response = self.client.post(
            reverse("signup"),
            data={
                "username": username,
                "email": email,
                "password1": password1,
                "password2": password2,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("send-mail-success"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        user = User.objects.get(email=email)
        self.assertIsNotNone(user)
        self.assertEqual(user.is_active, 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_verify_email(self):
        username = "user"
        email = "user@gmail.com"
        password1 = "admin@123"
        password2 = "admin@123"
        response = self.client.post(
            reverse("signup"),
            data={
                "username": username,
                "email": email,
                "password1": password1,
                "password2": password2,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("send-mail-success"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        user = User.objects.get(email=email)
        self.assertIsNotNone(user)
        token = EmailVerify.objects.get(user=user)
        response2 = self.client.post(
            reverse("verify-email", kwargs={"token": token.token}),
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(User.objects.get(email=email).is_active, 1)
        self.assertFalse(EmailVerify.objects.filter(user=user).exists())

    def test_token_is_not_exist(self):
        token = uuid.uuid4()
        response = self.client.post(
            reverse("verify-email", kwargs={"token": token}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/verify_email_fail.html")


class CommentViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pitch = PitchFactory(size="3")
        cls.user = UserFactory()
        cls.client = Client()

    def test_comment_creation_for_unauthenticated_user(self):
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.pk})
            + "?action=addcomment",
            {
                "submit_comment": True,
                "comment": "Comment by unauthenticated user",
                "rating": 4,
            },
        )
        response = self.client.get(
            reverse("pitch-detail", kwargs={"pk": self.pitch.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Comment.objects.filter(
                pitch=self.pitch,
                renter=self.user,
                comment="Comment by unauthenticated user",
            ).exists()
        )

    def test_access_comment_creation_for_user_with_no_order(self):
        AccessComment.objects.all().delete()
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.pk})
            + "?action=addcomment",
            {
                "submit_comment": True,
                "comment": "Access Comment for user with no order",
                "rating": 4,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AccessComment.objects.filter(
                pitch=self.pitch, renter=self.user, count_comment_created=0
            ).exists()
        )

    def test_access_comment_creation_for_user_with_order_unconfirmed(self):
        self.client.login(username=self.user.username, password="admin@123")
        start = timezone.now() + datetime.timedelta(hours=40)
        end = start + datetime.timedelta(hours=1)
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.id}),
            data={"time_start": start, "time_end": end},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.pk})
            + "?action=addcomment",
            {
                "submit_comment": True,
                "comment": "Access Comment for user with order not confirmed",
                "rating": 4,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Comment.objects.filter(
                pitch=self.pitch,
                renter=self.user,
                comment="Access Comment for user with order not confirmed",
            ).exists()
        )
        self.assertTrue(
            AccessComment.objects.filter(
                pitch=self.pitch, renter=self.user, count_comment_created=1
            ).exists()
        )

    def test_access_comment_creation_for_user_with_order_confirmed(self):
        self.client.login(username=self.user.username, password="admin@123")
        start = timezone.now() + datetime.timedelta(hours=40)
        end = start + datetime.timedelta(hours=1)
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.id}),
            data={"time_start": start, "time_end": end},
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(renter=self.user, pitch=self.pitch)
        order.status = "c"
        order.save()
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.pk})
            + "?action=addcomment",
            {
                "submit_comment": True,
                "comment": "Access Comment for user with confirmed order",
                "rating": 4,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            AccessComment.objects.filter(
                pitch=self.pitch, renter=self.user, count_comment_created=0
            ).exists()
        )
        self.assertTrue(
            Comment.objects.filter(
                pitch=self.pitch,
                renter=self.user,
                comment="Access Comment for user with confirmed order",
            ).exists()
        )

    def test_comment_creation_for_user_with_confirmed_order_but_not_logged_in(self):
        order = Order.objects.create(
            pitch=self.pitch, renter=self.user, status="c", cost=100
        )
        self.client.logout()
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.pk})
            + "?action=addcomment",
            {
                "submit_comment": True,
                "comment": "Comment for user with confirmed order (not logged in)",
                "rating": 4,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Comment.objects.filter(
                pitch=self.pitch,
                renter=self.user,
                comment="Comment for user with confirmed order (not logged in)",
            ).exists()
        )

    def test_comment_creation_for_user_with_confirmed_orders(self):
        self.client.login(username=self.user.username, password="admin@123")
        start = timezone.now() + datetime.timedelta(hours=40)
        end = start + datetime.timedelta(hours=1)
        response = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.id}),
            data={"time_start": start, "time_end": end},
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(renter=self.user, pitch=self.pitch)
        order.status = "c"
        order.save()
        self.client.login(username="testuser", password="testpass")
        response1 = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.pk})
            + "?action=addcomment",
            {
                "submit_comment": True,
                "comment": "Comment for user with confirmed order 1",
                "rating": 4,
            },
        )
        self.assertEqual(response1.status_code, 302)
        response2 = self.client.post(
            reverse("pitch-detail", kwargs={"pk": self.pitch.pk})
            + "?action=addcomment",
            {
                "submit_comment": True,
                "comment": "Attempted second comment for user with confirmed order",
                "rating": 5,
            },
        )
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(
            AccessComment.objects.filter(
                pitch=self.pitch, renter=self.user, count_comment_created=0
            ).exists()
        )
        self.assertFalse(
            Comment.objects.filter(
                pitch=self.pitch,
                renter=self.user,
                comment="Attempted second comment for user with confirmed order",
            ).exists()
        )
        self.assertEqual(Comment.objects.filter(renter=self.user).count(), 1)
