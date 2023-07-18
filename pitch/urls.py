from django.urls import include, path
from . import views
from project1 import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("list/", views.PitchListView.as_view(), name="pitch-list"),
    path("<int:pk>", views.PitchDetailView.as_view(), name="pitch-detail"),
]
