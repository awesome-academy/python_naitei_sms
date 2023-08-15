from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    CharField,
    ValidationError,
)
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _


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
