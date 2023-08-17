from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    CharField,
    ValidationError,
)
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _

from pitch.models import Favorite
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
    email = CharField(required=False)

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
