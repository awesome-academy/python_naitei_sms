from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:pk>/", views.pitch_detail, name="pitch-detail"),
    path("ordered/", views.MyOrderedView.as_view(), name="my-ordered"),
    path("ordered-detail/<int:pk>", views.order_cancel, name="order-detail"),
    path("search/", views.search_view, name="search"),
    path("upload-pitch-data/", views.upload_pitch_data, name="upload_pitch_data"),
    path(
        "pitch/<int:pk>/toggle_favorite/", views.toggle_favorite, name="toggle_favorite"
    ),
    path("favorite_pitches/", views.favorite_pitches, name="favorite_pitches"),
]
