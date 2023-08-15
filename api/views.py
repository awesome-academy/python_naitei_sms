import uuid
from django.http import BadHeaderError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from account.mail import send_mail_custom
from account.models import EmailVerify
from project1.settings import HOST
from .serialize import ChangePasswordSerializer, UserSerializer
from django.contrib.auth import login
from rest_framework import status
from django.utils.translation import gettext as _
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from rest_framework.generics import UpdateAPIView
from django.db import IntegrityError, transaction, DatabaseError


@api_view(["POST"])
def users_login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response(
            {"message": _("Account does not exist")},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if user.check_password(password):
        serializer = UserSerializer(user)
        login(request, user)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return Response(
            {
                "user": serializer.data,
                "access_token": access_token,
                "message": _("Login successful"),
                "status": status.HTTP_200_OK,
            }
        )
    else:
        return Response(
            {"message": _("Incorrect username or password")},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
def user_change_password(request):
    username = request.data.get("username")
    email = request.data.get("email")
    if username is None:
        return Response(
            {"message": _("Username is required")},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if email is None:
        return Response(
            {"message": _("Email is required")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = uuid.uuid4()
        link = HOST + reverse("verify-change-password", kwargs={"token": token})
        user = User.objects.get(username=username, email=email, is_active=True)
        send_mail_custom(
            _("Link to change password from Pitch App"),
            [email],
            None,
            "email/change_password.html",
            link=link,
            username=username,
        )
        EmailVerify.objects.create(token=token, user=user, type="1")
    except User.DoesNotExist:
        return Response(
            {"message": _("Username or Email is incorrect")},
            status=status.HTTP_404_NOT_FOUND,
        )
    except BadHeaderError:
        return Response(
            {"message": _("Email sending failed.")},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return Response(
        {
            "message": _("Password change link has been sent to your email"),
        }
    )


class ChangePasswordView(UpdateAPIView):
    serializer_class = ChangePasswordSerializer

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            token = kwargs.get("token")
            password = serializer.data.get("password")
            try:
                verify = EmailVerify.objects.get(token=token, type="1")

            except EmailVerify.DoesNotExist:
                return Response(
                    {
                        "message": _("Link is already in use or does not exist"),
                        "status": "error",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            verify = EmailVerify.objects.get(token=token, type="1")
            verify.user.password = make_password(password)

            try:
                with transaction.atomic():
                    verify.user.save()
                    verify.delete()
                    return Response(
                        {
                            "status": "success",
                            "code": status.HTTP_200_OK,
                            "message": "Password updated successfully",
                        }
                    )
            except Exception:
                return Response(
                    {
                        "message": _("Something went wrong"),
                        "status": "error",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {
                "status": "error",
                "errors": serializer.errors,
                "message": "The two password fields didn't match.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
