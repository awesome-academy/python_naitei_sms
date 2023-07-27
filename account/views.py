from django.shortcuts import render
from .forms import RegisterForm
from django.urls import reverse_lazy, reverse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
import uuid
from .models import EmailVerify
from account.mail import send_mail_custom
from project1.settings import HOST
from django.utils.translation import gettext
from django.views.decorators.csrf import csrf_protect


@csrf_protect
def sign_up(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            email = form.cleaned_data["email"]
            token = uuid.uuid4()

            link = HOST + reverse("verify-email", kwargs={"token": token})

            user = User.objects.create_user(username, email, password)
            user.is_active = False
            user.save()
            send_mail_custom(
                gettext("Verify your email from Pitch App"),
                email,
                None,
                "email/verify_email_signup.html",
                link=link,
                username=username,
            )

            EmailVerify.objects.create(user=user, token=token)

            return HttpResponseRedirect(reverse("send-mail-success"))
        else:
            return render(
                request,
                "registration/signup.html",
                {"form": form, "show_modal": False, "show_spinner_modal": False},
            )
    else:
        form = RegisterForm()
    return render(
        request,
        "registration/signup.html",
        {"form": form, "show_modal": False, "show_spinner_modal": False},
    )


def send_mail_success(request):
    context = {}
    return render(request, "registration/send_mail_success.html", context=context)


def verify_email(request, token):
    if EmailVerify.objects.filter(token=token).exists():
        userVerify = EmailVerify.objects.get(token=token)
        user = userVerify.user
        user.is_active = True
        user.save()
        userVerify.delete()
        return render(request, "registration/verify_email_success.html")
    else:
        return render(request, "registration/verify_email_fail.html")
