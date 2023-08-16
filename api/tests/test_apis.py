from django.test import TestCase
from pitch.factory import UserFactory
from django.test import Client
from django.urls import reverse_lazy, reverse
from django.core import mail
from account.models import EmailVerify


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
        self.assertEqual(response.status_code, 405)

    def test_username_password_is_valid(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="1")
        response2 = self.client.put(
            reverse("verify-change-password", kwargs={"token": token[0].token}),
            data={"password": "admin@123", "password_confirm": "admin@123"},
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 200)

    def test_username_and_email_is_none(self):
        response = self.client.post(
            reverse("user-change-password"),
        )
        self.assertEqual(response.status_code, 400)

    def test_username_does_not_exist(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": "username1234", "email": self.user.email},
        )
        self.assertEqual(response.status_code, 404)

    def test_email_is_invalid(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": "admin@example.com"},
        )
        self.assertEqual(response.status_code, 404)

    def test_password_is_invalid(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": "admin@example.com"},
        )
        self.assertEqual(response.status_code, 404)

    def test_password_is_none(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="1")
        response2 = self.client.put(
            reverse("verify-change-password", kwargs={"token": token[0].token}),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 400)

    def test_password_not_match(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="1")
        response2 = self.client.put(
            reverse("verify-change-password", kwargs={"token": token[0].token}),
            data={"password": "admin@123", "password_confirm": "admin@1234"},
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 400)

    def test_weak_password(self):
        response = self.client.post(
            reverse("user-change-password"),
            data={"username": self.user.username, "email": self.user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        token = EmailVerify.objects.filter(user=self.user, type="1")
        response2 = self.client.put(
            reverse("verify-change-password", kwargs={"token": token[0].token}),
            data={"password": "newpassword", "password_confirm": "newpassword"},
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 400)
