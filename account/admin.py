from django.contrib import admin
from account.models import EmailVerify
from project1.admin import my_admin_site


# Register your models here.
@admin.register(EmailVerify, site=my_admin_site)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "token",
    )
