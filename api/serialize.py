from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "is_active", "is_staff", "is_superuser", "date_joined"]
