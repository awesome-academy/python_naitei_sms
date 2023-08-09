import logging
import os
from MySQLdb import DatabaseError
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from account.mail import send_mail_custom
from django.utils import timezone

logger = logging.getLogger(__name__)


def mail_schedule_job():
    try:
        admins = User.objects.filter(is_superuser=1)
        emails = list(map(lambda x: x.email, admins))
        send_mail_custom(
            _("Monthly revenue statistics from Pitch App"),
            emails,
            None,
            "email/sale_statistics.html",
        )
        logger.info("Mail Schedule")
    except Exception as e:
        logger.error(e)
