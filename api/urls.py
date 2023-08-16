from django.urls import path
from . import views

urlpatterns = [
    path("users_login", views.users_login, name="users_login"),
    path(
        "user/change_password", views.user_change_password, name="user-change-password"
    ),
    path("user/change_info", views.ChangeInfoView.as_view(), name="user-change-info"),
    path(
        "user/change_password/<uuid:token>",
        views.ChangePasswordView.as_view(),
        name="verify-change-password",
    ),
    path("user_favorite_list/", views.user_favorite_list, name="user_favorite_list"),
    path(
        "toggle_favorite_pitch/<int:pitch_id>/",
        views.toggle_favorite_pitch,
        name="toggle-favorite-pitch"),
    path(
        "user/change_info/<uuid:token>",
        views.VerifyChangeInfoView.as_view(),
        name="verify-change-info",
    ),
    path(
        "statistic/revenue/",
        views.RevenueStatisticView.as_view(),
        name="api-revenue-statistic",
    ),
]
