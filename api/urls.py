from django.urls import path
from . import views

urlpatterns = [
    path("users_login", views.users_login, name="users_login"),
    path(
        "user/change_password", views.user_change_password, name="user_change_password"
    ),
    path(
        "user/change_password/<uuid:token>",
        views.ChangePasswordView.as_view(),
        name="verify-change-password",
    ),
]
