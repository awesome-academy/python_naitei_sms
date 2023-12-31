import uuid
from django.http import BadHeaderError
from rest_framework.response import Response
from django.contrib.auth.models import User
from account.mail import send_mail_custom
from account.models import EmailVerify
from pitch.models import Order, Pitch
from project1.settings import HOST
from .serialize import (
    ChangePasswordSerializer,
    OrderRateStatisticSerializer,
    RevenueStatisticSerializer,
    UserSerializer,
    VerifyChangeInfoSerializer,
    CommentSerializer,
    NestedCommentSerializer,
)
from django.contrib.auth import login
from rest_framework import status, permissions
from django.utils.translation import gettext as _
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from rest_framework.generics import UpdateAPIView
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from .serialize import UserSerializer, FavoritePitchSerializer
from pitch.models import Favorite, Pitch, User, Comment
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.db import IntegrityError, transaction, DatabaseError
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes
from django.contrib.sessions.models import Session
from django.db.models import Sum, Count
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination


@api_view(["POST"])
def users_login(request):
    session_id = request.COOKIES.get("sessionid")
    username = request.data.get("username")
    password = request.data.get("password")

    user = request.user
    if user.is_authenticated:
        return Response(
            {"message": _("You are already logged in.")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not session_id and not username:
        return Response(
            {"message": _("Username is required")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not session_id and not password:
        return Response(
            {"message": _("Password is required")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if session_id:
        try:
            session = Session.objects.get(session_key=session_id)
            user_id = session.get_decoded().get("_auth_user_id")
            user = User.objects.get(pk=user_id)
        except Session.DoesNotExist:
            user = None
    else:
        try:
            user = User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            return Response(
                {"message": _("Username does not exist or not verify yet")},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"message": _("Incorrect password")},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    serializer = UserSerializer(user)
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    if not session_id:
        login(request, user)
        return Response(
            {
                "user": serializer.data,
                "access_token": access_token,
                "message": _("Login successful"),
            },
            status=status.HTTP_201_CREATED,
        )
    else:
        return Response(
            {
                "user": serializer.data,
                "access_token": access_token,
                "message": _("Authenticated with session ID"),
                "status": status.HTTP_200_OK,
            }
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
                "message": _("The two password fields didn't match."),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ChangeInfoView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        user = request.user
        try:
            token = uuid.uuid4()
            link = HOST + reverse("verify-change-info", kwargs={"token": token})
            send_mail_custom(
                _("Link to change info from Pitch App"),
                [user.email],
                None,
                "email/change_info.html",
                link=link,
                username=user.username,
            )
            EmailVerify.objects.create(token=token, user=user, type="2")

        except BadHeaderError:
            return Response(
                {"message": _("Email sending failed.")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return Response(
            {
                "message": _("Info change link has been sent to your email"),
            }
        )


class VerifyChangeInfoView(UpdateAPIView):
    serializer_class = VerifyChangeInfoSerializer
    authentication_classes = [SessionAuthentication]

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            token = kwargs.pop("token")
            verify = EmailVerify.objects.get(token=token)
            try:
                with transaction.atomic():
                    if serializer.data.get("email"):
                        verify.user.email = serializer.data.get("email")
                    if serializer.data.get("first_name"):
                        verify.user.first_name = serializer.data.get("first_name")
                    if serializer.data.get("last_name"):
                        verify.user.last_name = serializer.data.get("last_name")
                    verify.user.save()
                    verify.delete()

                    return Response(
                        {
                            "message": _("Update info success!"),
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
                "message": _("Something went wrong."),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ChangeInfoView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        user = request.user
        try:
            token = uuid.uuid4()
            link = HOST + reverse("verify-change-info", kwargs={"token": token})
            send_mail_custom(
                _("Link to change info from Pitch App"),
                [user.email],
                None,
                "email/change_info.html",
                link=link,
                username=user.username,
            )
            EmailVerify.objects.create(token=token, user=user, type="2")

        except BadHeaderError:
            return Response(
                {"message": _("Email sending failed.")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return Response(
            {
                "message": _("Info change link has been sent to your email"),
            }
        )


class VerifyChangeInfoView(UpdateAPIView):
    serializer_class = VerifyChangeInfoSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            token = kwargs.pop("token")
            verify = EmailVerify.objects.get(token=token)
            try:
                with transaction.atomic():
                    if serializer.data.get("email"):
                        verify.user.email = serializer.data.get("email")
                    if serializer.data.get("first_name"):
                        verify.user.first_name = serializer.data.get("first_name")
                    if serializer.data.get("last_name"):
                        verify.user.last_name = serializer.data.get("last_name")
                    verify.user.save()
                    verify.delete()
                    serializer = UserSerializer(verify.user)

                    return Response(
                        {
                            "message": _("Update info success!"),
                            "data": serializer.data,
                        }
                    )

            except Exception:
                return Response(
                    {
                        "message": _("Something went wrong"),
                        "status": "error",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                "status": "error",
                "errors": serializer.errors,
                "message": _("Something went wrong."),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_favorite_list(request):
    user = request.user
    favorite_pitches = Favorite.objects.filter(renter=user)

    if not favorite_pitches.exists():
        return Response(
            {"message": "There are no favorite pitches."},
            status=status.HTTP_200_OK,
        )

    serializer = FavoritePitchSerializer(favorite_pitches, many=True)
    return Response({"Your favorite pitch list: ": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_favorite_pitch(request, pitch_id):
    user = request.user
    try:
        pitch = Pitch.objects.get(pk=pitch_id)
    except Pitch.DoesNotExist:
        return Response({"message": "Pitch not found."}, status=status.HTTP_200_OK)

    favorite, created = Favorite.objects.get_or_create(renter=user, pitch=pitch)

    if not created:
        favorite.delete()
        return Response(
            {"message": f"You unliked '{favorite.pitch.title}' pitch."},
            status=status.HTTP_200_OK,
        )
    return Response(
        {"message": f"You liked '{favorite.pitch.title}' pitch."},
        status=status.HTTP_200_OK,
    )


class RevenueStatisticView(APIView):
    serializer_class = RevenueStatisticSerializer

    permission_classes = [
        IsAdminUser,
    ]

    def get(self, request, *args, **kwargs):
        params = request.GET.items()
        params_list = list()
        param_pitch = list()
        for param in params:
            if param[1] != None and param[1] != "":
                if (
                    param[0].startswith("size")
                    or param[0].startswith("surface")
                    or param[0].startswith("price")
                ):
                    param_pitch.append(param)
                elif param[0].startswith("order"):
                    params_list.append(param)

        query = dict((x, y) for x, y in params_list)
        query_pitch = dict((x, y) for x, y in param_pitch)

        revenues = Pitch.objects.annotate(
            revenue=Sum("order__cost", filter=Q(**query)),
            count_order=Count("order", filter=Q(**query)),
        ).filter(**query_pitch)

        serializer = RevenueStatisticSerializer(revenues, many=True)

        return Response(
            {
                "status": "success",
                "code": status.HTTP_200_OK,
                "data": serializer.data,
                "message": "Revenue Statistic!",
            }
        )


class OrderRateStatisticView(APIView):
    permission_classes = [
        IsAdminUser,
    ]

    def get(self, request, *args, **kwargs):
        params = request.GET.items()
        params_list = list()
        for param in params:
            if (
                param[1] != None
                and param[1] != ""
                and (
                    param[0].startswith("size")
                    or param[0].startswith("surface")
                    or param[0].startswith("price")
                )
            ):
                params_list.append(param)

        query = dict((x, y) for x, y in params_list)
        total_orders = Order.objects.filter(status="c").count() * 1.00

        rates = Pitch.objects.annotate(
            rate=Count("order", filter=Q(order__status="c")) * 1.00 / total_orders
        ).filter(**query)

        serializer = OrderRateStatisticSerializer(rates, many=True)

        return Response(
            {
                "status": "success",
                "code": status.HTTP_200_OK,
                "data": serializer.data,
                "message": "Order Rate Statistic!",
            }
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_reply_view(request, comment_id):
    try:
        parent_comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        return Response(
            {"error": "Parent comment not found"}, status=status.HTTP_404_NOT_FOUND
        )
    pitch_id = parent_comment.pitch_id
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(
            renter=request.user, parent_id=parent_comment.id, pitch_id=pitch_id
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def list_comments_pitch_view(request, pitch_id):
    sort = request.query_params.get("sort")
    limit = request.query_params.get("limit")
    page = request.query_params.get("page")

    comments = Comment.objects.filter(pitch_id=pitch_id, parent=None).order_by(
        "created_date" if sort == "desc" else "-created_date"
    )

    if not comments.exists():
        return Response(
            {"message": "There are no comments."},
            status=status.HTTP_200_OK,
        )
    paginator = PageNumberPagination()
    try:
        limit = int(limit)
    except Exception:
        limit = 10

    paginator.page_size = limit
    paginator.page = page

    result_page = paginator.paginate_queryset(comments, request)

    serializer = NestedCommentSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)
