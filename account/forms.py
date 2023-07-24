from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class RegisterForm(UserCreationForm):
    def clean_password(self):
        pwd1 = self.cleaned_data["password1"]
        pwd2 = self.cleaned_data["password2"]

        # Check if a date is not in the past.
        if pwd1 != pwd2:
            raise ValidationError("password incorrect")
        return pwd1

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise ValidationError("username exists")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(email=email).exists():
            raise ValidationError("email exists")
        return email

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
