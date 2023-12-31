from django.urls import include, path
from . import views

urlpatterns = [
    path("signup/", views.sign_up, name="signup"),
    path("signup/send-mail-success", views.send_mail_success, name="send-mail-success"),
    path("verify_email/<uuid:token>", views.verify_email, name="verify-email"),
]
