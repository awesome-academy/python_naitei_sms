from django.urls import include, path
from . import views
urlpatterns = [
    path('users_login', views.users_login, name='users_login'),
]
