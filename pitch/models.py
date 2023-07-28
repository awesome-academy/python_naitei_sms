from django.db import models
from django.contrib.auth.models import User
from pitch.constant import SIZE, SURFACE_GRASS, STATUS_ORDER
from django.core.validators import MaxValueValidator, MinValueValidator
from django.urls import reverse
from django.utils import timezone

# Create your models here.


class Voucher(models.Model):
    name = models.CharField(max_length=200)
    min_cost = models.PositiveIntegerField(
        validators=[MaxValueValidator(20000000), MinValueValidator(0)]
    )
    discount = models.PositiveIntegerField(
        validators=[MaxValueValidator(200000000), MinValueValidator(0)]
    )
    count = models.PositiveIntegerField(
        validators=[MaxValueValidator(200000), MinValueValidator(1)]
    )

    class Meta:
        db_table = "vouchers"

    def __str__(self):
        return self.name


class Pitch(models.Model):
    address = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, null=True)
    phone = models.CharField(max_length=100, null=True)
    avg_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MaxValueValidator(5), MinValueValidator(0)],
        default=0,
    )
    size = models.CharField(
        max_length=1,
        choices=SIZE,
        blank=True,
        default="1",
        help_text="Types of football fields",
    )
    surface = models.CharField(
        max_length=1,
        choices=SURFACE_GRASS,
        blank=True,
        default="n",
        help_text="Types of surface grass",
    )
    price = models.PositiveIntegerField(
        validators=[MaxValueValidator(2000000000), MinValueValidator(0)]
    )

    class Meta:
        ordering = ["price", "size"]
        db_table = "pitches"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("pitch-detail", args=[str(self.id)])

    def get_label_grass(self):
        for grass in SURFACE_GRASS:
            if grass[0] == self.surface:
                return grass[1]
        return ""

    def get_label_size(self):
        for size in SIZE:
            if size[0] == self.size:
                return size[1]
        return ""


class Order(models.Model):
    time_start = models.DateTimeField(null=False, blank=False, default=timezone.now())
    time_end = models.DateTimeField(null=False, blank=False, default=timezone.now())
    status = models.CharField(
        max_length=1,
        choices=STATUS_ORDER,
        blank=True,
        default="o",
        help_text="Types of surface grass",
    )
    price = models.PositiveIntegerField(
        validators=[MaxValueValidator(2000000000), MinValueValidator(0)], default=0
    )
    renter = models.ForeignKey(User, on_delete=models.CASCADE)
    voucher = models.ForeignKey(
        Voucher, on_delete=models.CASCADE, null=True, blank=True
    )
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE)
    cost = models.PositiveBigIntegerField(
        validators=[MaxValueValidator(20000000000), MinValueValidator(0)]
    )
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders"
        ordering = ["created_date", "cost"]

    def __str__(self):
        return f"Order {self.pk} - {self.renter.username}"


class Comment(models.Model):
    renter = models.ForeignKey(User, on_delete=models.CASCADE)
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE)
    rating = models.IntegerField(
        default=5, validators=[MaxValueValidator(5), MinValueValidator(1)]
    )
    comment = models.CharField(max_length=500)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comments"
        ordering = ["created_date"]

    def __str__(self):
        return f"Comment {self.pk} - {self.renter.username}"


class Image(models.Model):
    image = models.ImageField(
        upload_to="uploads",
        default="default-image.jpg",
        null=False,
        help_text="Image of the pitch",
    )
    pitch = models.ForeignKey(Pitch, related_name="image", on_delete=models.CASCADE)

    class Meta:
        db_table = "images"
