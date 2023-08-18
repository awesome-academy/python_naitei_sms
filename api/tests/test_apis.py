from django.test import TestCase
from pitch.factory import UserFactory, PitchFactory
from django.test import Client
from django.urls import reverse
from django.core import mail
from account.models import EmailVerify
from rest_framework.test import APIClient
from rest_framework import status
from pitch.models import Favorite
from api.serialize import FavoritePitchSerializer
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User


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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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
