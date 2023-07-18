from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from .forms import RegisterForm


def sign_up(request):
    if request.method == "GET":
        form = RegisterForm()
        return render(request, "registration/signup.html", {"form": form})
