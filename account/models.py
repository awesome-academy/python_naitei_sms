from django.db import models
from django.contrib.auth.models import User
import uuid


# Create your models here.
class EmailVerify(models.Model):
    user = models.ForeignKey(User, unique=True, on_delete=models.CASCADE)
    token = models.UUIDField(
        default=uuid.uuid4,
    )

    def get_url_verify_email(self):
        return
