from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    CharField,
    ValidationError,
    IntegerField,
    DecimalField,
    EmailField,
)
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
import pitch

from pitch.models import Order, Pitch

from pitch.models import Favorite, Comment
from rest_framework import serializers


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_name",
            "first_name",
        ]


class ChangePasswordSerializer(Serializer):
    password = CharField(required=True)
    password_confirm = CharField(required=True)

    def validate(self, data):
        validate_password(data["password"])
        validate_password(data["password_confirm"])

        if data["password"] != data["password_confirm"]:
            raise ValidationError(
                {"password_confirm": _("The two password fields didn't match.")}
            )

        return data


class FavoritePitchSerializer(ModelSerializer):
    pitch_title = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ["pitch", "pitch_title"]

    def get_pitch_title(self, favorite_instance):
        return favorite_instance.pitch.title if favorite_instance.pitch else None


class VerifyChangeInfoSerializer(Serializer):
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    email = EmailField(required=False)

    def validate(self, data):
        if (
            data.get("email") == None
            and data.get("first_name") == None
            and data.get("last_name") == None
        ):
            raise ValidationError(
                {"fields": _("Minimum field required for email, first_name, last_name")}
            )

        return data


class RevenueStatisticSerializer(ModelSerializer):
    revenue = IntegerField()
    count_order = IntegerField()

    class Meta:
        model = Pitch
        fields = ["id", "title", "revenue", "size", "surface", "price", "count_order"]


class OrderRateStatisticSerializer(ModelSerializer):
    rate = DecimalField(
        max_digits=2,
        decimal_places=2,
    )

    class Meta:
        model = Pitch
        fields = ["id", "title", "rate", "size", "surface", "price"]


class NestedCommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(source="renter", read_only=True)
    created_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "comment", "user", "created_date", "replies"]

    def get_replies(self, obj):
        if obj.replies.exists():
            serializer = NestedCommentSerializer(obj.replies.all(), many=True)
            return serializer.data
        return None


class CommentSerializer(serializers.ModelSerializer):
    renter_id = serializers.IntegerField(source="renter.id", read_only=True)
    parent_id = serializers.IntegerField(
        source="parent.id", read_only=True, required=False
    )
    pitch_id = serializers.IntegerField(write_only=True, required=False)
    replies = NestedCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "comment", "renter_id", "parent_id", "replies", "pitch_id"]
