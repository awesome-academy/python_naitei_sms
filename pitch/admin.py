from django.contrib import admin
from .models import Voucher, Pitch, Order, Comment, Image


class ImageInline(admin.TabularInline):
    model = Image


@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    list_display = ("address", "title", "description", "size", "surface", "price")
    fields = [("address"), ("title"), ("size"), ("surface"), ("price"), ("description")]
    inlines = [ImageInline]
    list_filter = ("size", "surface", "price")


# Register the Admin classes for Book using the decorator


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ("name", "min_cost", "discount", "count")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "renter",
        "pitch",
        "rating",
        "comment",
        "created_date",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "time_start",
        "time_end",
        "status",
        "renter",
        "voucher",
        "cost",
        "created_date",
    )
