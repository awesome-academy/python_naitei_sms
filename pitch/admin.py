from django.contrib import admin, messages
from .models import Voucher, Pitch, Order, Comment, Image
from .models import Pitch

class ImageInline(admin.TabularInline):
    model = Image


@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    list_display = ("address", "title", "description", "size", "surface", "price")
    fields = [
        ("address"),
        ("title"),
        ("size"),
        ("phone"),
        ("surface"),
        ("price"),
        ("description"),
    ]
    inlines = [ImageInline]
    list_filter = ("size", "surface", "price")

    def has_pending_or_future_orders(self, obj):
        return obj.order_set.filter(status__in=['o']).exists()

    def delete_model(self, request, obj):
        if obj.has_pending_or_future_orders():
            messages.error(request, "Cannot delete this pitch because there are pending or future orders associated with it.")
        else:
            super().delete_model(request, obj)

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
        "status",
        "renter",
        "time_start",
        "time_end",
        "cost",
        "created_date",
    )
