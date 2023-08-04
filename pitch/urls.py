from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:pk>", views.pitch_detail, name="pitch-detail"),
    path("ordered/", views.MyOrderedView.as_view(), name="my-ordered"),
    path("ordered-detail/<int:pk>", views.order_cancel, name="order-detail"),
    path('search/', views.search_view, name='search'),
    path('create-comment/<int:pk>/', views.create_comment, name='create-comment'),
]
