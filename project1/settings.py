import os
from django.utils.translation import gettext_lazy as _
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
IS_PRODUCT = int(os.environ.get("PRODUCT", 0)) == 1
HOST_MYSQL = "mysql" if IS_PRODUCT else "localhost"


SECRET_KEY = os.environ.get(
    "SECRET_KEY", "cg#p$g+j9tax!#a3cup@1$8obt2_+&k3q+pmu)5%asj6yjpkag"
)

DEBUG = not IS_PRODUCT
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False if DEBUG else True,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "log/info.log"),
            "formatter": "verbose",
        },
        "file_log": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "log/error.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file_log"],
            "propagate": True,
            "level": "DEBUG",
        },
        "pitch": {
            "handlers": ["file"],
            "level": "INFO",
        },
    },
}

ALLOWED_HOSTS = ["*"]

SECURE_SSL_REDIRECT = IS_PRODUCT
SESSION_COOKIE_SECURE = IS_PRODUCT
CSRF_COOKIE_SECURE = IS_PRODUCT
SECURE_HSTS_SECONDS = IS_PRODUCT * 7200


INSTALLED_APPS = [
    "project1.apps.MyAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pitch.apps.PitchConfig",
    "account.apps.AccountConfig",
    "api.apps.ApiConfig",
    "jquery",
    "bootstrap_datepicker_plus",
    "bootstrap5",
    "compressor",
    "django_crontab",
    "rest_framework",
    "chartjs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

ROOT_URLCONF = "project1.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "project1.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("NAME_DB"),
        "USER": os.getenv("USER_DB"),
        "PASSWORD": os.getenv("PASS_DB"),
        "HOST": HOST_MYSQL,
        "PORT": os.getenv("PORT_DB"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGES = [
    ("en", _("English")),
    ("vi", _("Vietnamese")),
]

TIME_ZONE = "Asia/Ho_Chi_Minh"

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles/"
MEDIA_ROOT = BASE_DIR / "media/"
MEDIA_URL = "/media/"
STATICFILES_DIRS = [
    BASE_DIR / "static/",
]


STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("MAIL")
EMAIL_HOST_PASSWORD = os.getenv("PASS")
DEFAULT_FROM_EMAIL = os.getenv("MAIL")
EMAIL_FILE_PATH = "/tmp/app-messages"

CRONJOBS = [("*/1 * * * *", "pitch.cron.mail_schedule_job")]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

HOST = "http://localhost:8000" if IS_PRODUCT else "http://localhost:8000"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "USER_ID_FIELD": "id",
}
