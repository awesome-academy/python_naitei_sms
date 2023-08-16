from django.db import models
from django.contrib.auth.models import User
import uuid

from pitch.constant import TYPE_TOKEN


# Create your models here.
class EmailVerify(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(
        default=uuid.uuid4,
    )
    type = models.CharField(
        max_length=1,
        choices=TYPE_TOKEN,
        blank=True,
        default="0",
        help_text="Types of token",
    )

    def get_url_verify_email(self):
        return
