from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("list/", views.PitchListView.as_view(), name="pitch-list"),
    path("ordered/", views.MyOrderedView.as_view(), name="my-ordered"),
    path("<int:pk>", views.pitch_detail, name="pitch-detail"),
]
