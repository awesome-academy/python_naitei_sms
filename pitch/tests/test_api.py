from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from pitch import *
from django.contrib.sessions.models import Session


class UserAuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = "testuser"
        self.password = "testpass"
        self.user = User.objects.create_user(
            username=self.username, password=self.password, is_active=True
        )
        self.usernamenotactive = "testusernotactive"
        self.passwordnotactive = "testpassnotactive"
        self.user = User.objects.create_user(
            username=self.usernamenotactive,
            password=self.passwordnotactive,
            is_active=False,
        )

    def test_login_with_session_id(self):
        self.client.login(username=self.username, password=self.password)
        session = Session.objects.get(session_key=self.client.session.session_key)

        response = self.client.post(
            reverse("users_login"), {"session_id": session.session_key}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Authenticated with session ID")

        response = self.client.get(reverse("my-ordered"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_url_with_invalid_session_id(self):
        session_id = "invalid_session_id"
        self.client.cookies["sessionid"] = session_id
        response = self.client.get(reverse("my-ordered"))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/accounts/login/", response.url)

    def test_login_and_access_protected_url(self):
        login_data = {"username": self.username, "password": self.password}
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
        login_data = {"username": "nonexistentuser", "password": self.password}
        response = self.client.post(reverse("users_login"), login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)
        self.assertEqual(
            response.data["message"], "Username does not exist or not verify yet"
        )

    def test_invalid_credentials(self):
        login_data = {"username": self.username, "password": "wrongpass"}
        response = self.client.post(reverse("users_login"), login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Incorrect password")

    def test_user_not_active(self):
        login_data = {
            "username": self.usernamenotactive,
            "password": self.passwordnotactive,
        }
        response = self.client.post(reverse("users_login"), login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("message", response.data)
        self.assertEqual(
            response.data["message"], "Username does not exist or not verify yet"
        )
