from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf.urls.static import static
from project1 import settings
from project1.admin import my_admin_site

urlpatterns = [
    path("", RedirectView.as_view(url="pitch/")),
    path("admin/", my_admin_site.urls),
    path("pitch/", include("pitch.urls")),
    path("accounts/", include("account.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", RedirectView.as_view(url="login/")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/", include("api.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# accounts/ login/ [name='login']
# accounts/ logout/ [name='logout']
# accounts/ password_change/ [name='password_change']
# accounts/ password_change/done/ [name='password_change_done']
# accounts/ password_reset/ [name='password_reset']
# accounts/ password_reset/done/ [name='password_reset_done']
# accounts/ reset/<uidb64>/<token>/ [name='password_reset_confirm']
# accounts/ reset/done/ [name='password_reset_complete']
