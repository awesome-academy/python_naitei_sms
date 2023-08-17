from django.test import TestCase
from pitch.factory import OrderFactory, PitchFactory, UserFactory, CommentFactory
from django.test import Client
from django.urls import reverse
from django.core import mail
from account.models import EmailVerify
from rest_framework.test import APIClient
from rest_framework import status
from api.serialize import FavoritePitchSerializer
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
import datetime
from django.utils import timezone
from pitch.models import Favorite, Comment, Order


class UserAuthenticationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.client = Client()

    def test_login_when_already_authenticated(self):
        self.client.login(username=self.user.username, password="admin@123")

        response = self.client.post(
            reverse("users_login"),
            data={"username": self.user.username, "password": "admin@123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "You are already logged in.")

    def test_login_with_session_id(self):
        self.client.login(username=self.user.username, password="admin@123")
        session = Session.objects.get(session_key=self.client.session.session_key)
        self.client.logout()
        response = self.client.post(
            reverse("users_login"),
            {
                "session_id": session.session_key,
                "username": self.user.username,
                "password": "admin@123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Login successful")

        response = self.client.get(reverse("my-ordered"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_url_with_invalid_session_id(self):
        session_id = "invalid_session_id"
        self.client.cookies["sessionid"] = session_id
        response = self.client.get(reverse("my-ordered"))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/accounts/login/", response.url)

    def test_login_and_access_protected_url(self):
        login_data = {"username": self.user.username, "password": "admin@123"}
        response = self.client.post(reverse("users_login"), login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("access_token", response.data)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Login successful")
        response = self.client.get(reverse("my-ordered"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_without_session_id_and_empty_fields(self):
        login_data = {"username": "", "password": ""}
        response = self.client.post(reverse("users_login"), login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Username is required")

    def test_access_protected_url_without_login(self):
        response = self.client.get(reverse("my-ordered"))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/accounts/login/", response.url)

    def test_user_not_exists(self):
        login_data = {"username": "nonexistentuser", "password": "admin@123"}
        response = self.client.post(reverse("users_login"), login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)
        self.assertEqual(
            response.data["message"], "Username does not exist or not verify yet"
        )

    def test_invalid_credentials(self):
        login_data = {"username": self.user.username, "password": "wrongpass"}
        response = self.client.post(reverse("users_login"), login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Incorrect password")

    def test_user_not_active(self):
        self.user.is_active = False
        self.user.save()
        login_data = {
            "username": self.user.username,
            "password": "admin@123",
        }
        response = self.client.post(reverse("users_login"), login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)
        self.assertEqual(
            response.data["message"], "Username does not exist or not verify yet"
        )


class ChangePasswordApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.client = Client()

    def test_method_is_get(self):
        response = self.client.get(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"].code, "method_not_allowed")

    def test_username_password_is_valid(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Password change link has been sent to your email"
        )
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="1")
        response2 = self.client.put(
            reverse("verify-change-password", kwargs={"token": token[0].token}),
            data={"password": "admin@123", "password_confirm": "admin@123"},
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["message"], "Password updated successfully")

    def test_username_and_email_is_none(self):
        response = self.client.post(
            reverse("user-change-password"),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Username is required")

    def test_username_does_not_exist(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": "username1234", "email": self.user.email},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Username or Email is incorrect")

    def test_email_is_invalid(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": "admin@example.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Username or Email is incorrect")

    def test_password_is_invalid(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": "admin@example.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Username or Email is incorrect")

    def test_password_is_none(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Password change link has been sent to your email"
        )
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="1")
        response2 = self.client.put(
            reverse("verify-change-password", kwargs={"token": token[0].token}),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response2.data["message"],
            "The two password fields didn't match.",
        )

    def test_password_not_match(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Password change link has been sent to your email"
        )
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="1")
        response2 = self.client.put(
            reverse("verify-change-password", kwargs={"token": token[0].token}),
            data={"password": "admin@123", "password_confirm": "admin@1234"},
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response2.data["message"],
            "The two password fields didn't match.",
        )

    def test_weak_password(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Password change link has been sent to your email"
        )
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="1")
        response2 = self.client.put(
            reverse("verify-change-password", kwargs={"token": token[0].token}),
            data={"password": "newpassword", "password_confirm": "newpassword"},
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response2.data["errors"])


class ToggleFavoritePitchTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = UserFactory()
        cls.pitch = PitchFactory(size="3")

    def test_toggle_favorite_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("toggle-favorite-pitch", args=[self.pitch.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["message"], f"You liked '{self.pitch.title}' pitch."
        )

        list_response = self.client.get(reverse("user_favorite_list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data["Your favorite pitch list: "]), 1)
        self.assertEqual(
            list_response.data["Your favorite pitch list: "][0]["pitch"], self.pitch.id
        )

        response = self.client.post(
            reverse("toggle-favorite-pitch", args=[self.pitch.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["message"], f"You unliked '{self.pitch.title}' pitch."
        )

        list_response = self.client.get(reverse("user_favorite_list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(
            list_response.data["message"], "There are no favorite pitches."
        )

    def test_toggle_favorite_unauthenticated(self):
        self.client.logout()

        response = self.client.post(
            reverse("toggle-favorite-pitch", args=[self.pitch.id])
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_toggle_favorite_nonexistent_pitch(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("toggle-favorite-pitch", args=[999]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Pitch not found.")


class UserFavoriteListTestCase(TestCase):
    def setUp(cls):
        cls.client = APIClient()
        cls.user = UserFactory()
        cls.pitch = PitchFactory(size="3")

    def test_user_favorite_list_unauthenticated(self):
        response = self.client.get(reverse("user_favorite_list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_favorite_list_empty(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("user_favorite_list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {"message": "There are no favorite pitches."},
        )

    def test_user_favorite_list_non_empty(self):
        self.client.force_login(self.user)
        favorite_pitch = Favorite.objects.create(renter=self.user, pitch=self.pitch)
        response = self.client.get(reverse("user_favorite_list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "Your favorite pitch list: ": [
                    FavoritePitchSerializer(favorite_pitch).data
                ]
            },
        )


class ChangeInfoApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.client = Client()

    def test_not_login(self):
        response = self.client.post(
            reverse("user-change-info"),
        )

    def test_method_is_get(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(
            reverse("user-change-info"),
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"].code, "method_not_allowed")

    def test_request_change_info_is_valid(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("user-change-info"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Info change link has been sent to your email"
        )
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="2")
        response2 = self.client.put(
            reverse("verify-change-info", kwargs={"token": token[0].token}),
            data={
                "email": "admin123@gmail.com",
                "first_name": "admin",
                "last_name": "user",
            },
            content_type="application/json",
        )
        user = User.objects.get(id=self.user.id)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(user.email, "admin123@gmail.com")
        self.assertEqual(user.first_name, "admin")
        self.assertEqual(user.last_name, "user")
        self.assertEqual(response2.data["message"], "Update info success!")

    def test_request_change_only_email(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("user-change-info"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Info change link has been sent to your email"
        )
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="2")
        response2 = self.client.put(
            reverse("verify-change-info", kwargs={"token": token[0].token}),
            data={
                "email": "admin123@gmail.com",
            },
            content_type="application/json",
        )
        user = User.objects.get(id=self.user.id)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(user.email, "admin123@gmail.com")
        self.assertEqual(response2.data["message"], "Update info success!")

    def test_change_info_body_is_none(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("user-change-info"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Info change link has been sent to your email"
        )
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="2")
        response2 = self.client.put(
            reverse("verify-change-info", kwargs={"token": token[0].token}),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response2.data["message"], "Something went wrong.")
        self.assertIsNotNone(response2.data["errors"])

    def test_email_is_valid(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("user-change-info"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Info change link has been sent to your email"
        )
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="2")
        response2 = self.client.put(
            reverse("verify-change-info", kwargs={"token": token[0].token}),
            data={
                "email": "admin123",
            },
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response2.data["message"], "Something went wrong.")
        self.assertIsNotNone(response2.data["errors"])


class RevenueStatisticApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=False, is_staff=False)
        cls.admin = UserFactory(is_superuser=True)
        cls.pitch_size_small = PitchFactory(size="1", price=1)
        cls.pitch_size_normal = PitchFactory(size="2", price=1)
        cls.orders = []
        for i in range(0, 20):
            cls.orders.append(
                OrderFactory(
                    renter=cls.user,
                    pitch=cls.pitch_size_small if i < 10 else cls.pitch_size_normal,
                    time_start=timezone.now() + datetime.timedelta(hours=i + 1)
                    if i < 10
                    else timezone.now()
                    + datetime.timedelta(hours=i + 1)
                    + datetime.timedelta(days=1),
                    status="c",
                )
            )
        cls.client = Client()

    def test_not_login(self):
        response = self.client.post(
            reverse("api-revenue-statistic"),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_login_is_user(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(
            reverse("api-revenue-statistic"),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_login_is_admin(self):
        self.client.login(username=self.admin.username, password="admin@123")
        response = self.client.get(
            reverse("api-revenue-statistic"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Revenue Statistic!")
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(response.data["data"][0]["revenue"], 10)

    def test_filter_pitch_by_size(self):
        self.client.login(username=self.admin.username, password="admin@123")
        response = self.client.get(
            reverse("api-revenue-statistic"), QUERY_STRING="size=1"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Revenue Statistic!")
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["revenue"], 10)

    def test_filter_order_by_time(self):
        start = timezone.now()
        end = timezone.now() + datetime.timedelta(hours=20)
        query = "order__time_start__gte=%s&order__time_end__lte=%s" % (
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.client.login(username=self.admin.username, password="admin@123")
        response = self.client.get(reverse("api-revenue-statistic"), QUERY_STRING=query)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Revenue Statistic!")
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(response.data["data"][0]["revenue"], 10)
        self.assertEqual(response.data["data"][1]["revenue"], None)

    def test_filter_order_by_time_and_pitch_size(self):
        start = timezone.now()
        end = timezone.now() + datetime.timedelta(hours=20)
        query = "order__time_start__gte=%s&order__time_end__lte=%s&size=1" % (
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.client.login(username=self.admin.username, password="admin@123")
        response = self.client.get(reverse("api-revenue-statistic"), QUERY_STRING=query)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Revenue Statistic!")
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["revenue"], 10)


class OrderRateStatisticApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=False, is_staff=False)
        cls.admin = UserFactory(is_superuser=True)
        cls.pitch_size_small = PitchFactory(size="1", price=1)
        cls.pitch_size_normal = PitchFactory(size="2", price=1)
        cls.orders = []
        for i in range(0, 20):
            cls.orders.append(
                OrderFactory(
                    renter=cls.user,
                    pitch=cls.pitch_size_small if i < 10 else cls.pitch_size_normal,
                    time_start=timezone.now() + datetime.timedelta(hours=i + 1)
                    if i < 10
                    else timezone.now()
                    + datetime.timedelta(hours=i + 1)
                    + datetime.timedelta(days=1),
                    status="c",
                )
            )
        cls.client = Client()

    def test_not_login(self):
        response = self.client.post(
            reverse("api-statistic-order-rate"),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_login_is_user(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.get(
            reverse("api-statistic-order-rate"),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_login_is_admin(self):
        self.client.login(username=self.admin.username, password="admin@123")
        response = self.client.get(
            reverse("api-statistic-order-rate"),
        )
        orders = Order.objects.filter(status="c").count() * 1.00
        orders_pitch_small = (
            Order.objects.filter(status="c", pitch=self.pitch_size_small).count() * 1.00
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Order Rate Statistic!")
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(
            float(response.data["data"][0]["rate"]), float(orders_pitch_small / orders)
        )

    def test_filter_pitch_by_size(self):
        self.client.login(username=self.admin.username, password="admin@123")
        response = self.client.get(
            reverse("api-statistic-order-rate"), QUERY_STRING="size=1"
        )
        orders = Order.objects.filter(status="c").count() * 1.00
        orders_pitch_small = (
            Order.objects.filter(status="c", pitch=self.pitch_size_small).count() * 1.00
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Order Rate Statistic!")
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(
            float(response.data["data"][0]["rate"]), float(orders_pitch_small / orders)
        )


class ReplyCommentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = UserFactory()
        cls.pitch = PitchFactory(size="3")
        cls.comment = CommentFactory()

    def test_reply_comment_unauthenticated(self):
        self.client.logout()

        response = self.client.post(reverse("create-reply", args=[self.comment.id]))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_create_reply_success(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("create-reply", args=[self.comment.id]),
            {"comment": "This is a reply."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)
        new_reply = Comment.objects.last()
        self.assertEqual(new_reply.renter, self.user)
        self.assertEqual(new_reply.pitch, self.comment.pitch)
        self.assertEqual(new_reply.parent, self.comment)
        self.assertEqual(new_reply.comment, "This is a reply.")

    def test_create_reply_parent_not_found(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("create-reply", args=[999]),
            {"comment": "This is a reply."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Comment.objects.count(), 1)

    def test_create_reply_invalid_data(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("create-reply", args=[self.comment.id]),
            {"invalid_field": "Invalid value"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Comment.objects.count(), 1)

    def test_create_reply_blank_comment(self):
        self.client.login(username=self.user.username, password="admin@123")
        response = self.client.post(
            reverse("create-reply", args=[self.comment.id]),
            {"comment": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Comment.objects.count(), 1)

    def test_create_reply_parent_with_reply(self):
        self.client.login(username=self.user.username, password="admin@123")
        reply = CommentFactory(parent=self.comment, pitch=self.comment.pitch)
        response = self.client.post(
            reverse("create-reply", args=[reply.id]),
            {"comment": "This is a reply to a reply 1."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 3)
        new_reply = Comment.objects.last()

        self.assertEqual(new_reply.renter, self.user)
        self.assertEqual(new_reply.pitch, self.comment.pitch)
        self.assertEqual(new_reply.parent, reply)
        self.assertEqual(new_reply.comment, "This is a reply to a reply 1.")


class ListCommentsPitchViewTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.pitch = PitchFactory()
        cls.comments = CommentFactory.create_batch(10, pitch=cls.pitch)
        cls.replies = CommentFactory.create_batch(5, parent=cls.comments[0])

    def test_list_comments_no_limit_and_page_sort(self):
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)

    def test_list_comments_with_nested_structure(self):
        sort = "desc"
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(url, QUERY_STRING="sort=%s" % (sort))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(len(response.data["results"][0]["replies"]), 5)

    def test_list_comments_invalid_limit_return_defaultlimit(self):
        limit = "invalid"
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(url, QUERY_STRING="limit=%s" % (limit))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)

    def test_list_comments_invalid_sort_return_defaultsort(self):
        sort = "invalid"
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(url, QUERY_STRING="sort=%s" % (sort))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertTrue(
            response.data["results"][0]["created_date"]
            >= response.data["results"][1]["created_date"]
        )

    def test_list_comments_invalid_page(self):
        page = "invalid"
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(url, QUERY_STRING="page=%s" % (page))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Invalid page.")

    def test_list_comments_pagination(self):
        limit = 3
        page = 2
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(url, QUERY_STRING="limit=%d&page=%d" % (limit, page))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), limit)
        if page - 1 == 1:
            self.assertEqual(
                response.data["previous"],
                f"http://testserver{url}?limit={limit}",
            )
        else:
            self.assertEqual(
                response.data["previous"],
                f"http://testserver{url}?limit={limit}&page={page - 1}",
            )
        self.assertEqual(
            response.data["next"],
            f"http://testserver{url}?limit={limit}&page={page + 1}",
        )

    def test_list_comments_sort_asc(self):
        limit = 5
        page = 1
        sort = "asc"
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(
            url, QUERY_STRING="sort=%s&limit=%d&page=%d" % (sort, limit, page)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), limit)
        self.assertTrue(
            response.data["results"][0]["created_date"]
            >= response.data["results"][1]["created_date"]
        )

    def test_list_comments_sort_desc(self):
        limit = 2
        page = 1
        sort = "desc"
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(
            url, QUERY_STRING="sort=%s&limit=%d&page=%d" % (sort, limit, page)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), limit)
        self.assertTrue(
            response.data["results"][0]["created_date"]
            <= response.data["results"][1]["created_date"]
        )

    def test_list_comments_no_comments(self):
        Comment.objects.all().delete()
        url = reverse("list-pitch-comments", args=[self.pitch.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "There are no comments.")
