from pathlib import Path
from datetime import timedelta
from settings.conf import *
from celery.schedules import crontab
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = SECRET_KEY  # noqa: F811 (from conf)

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    "channels",
    "django_celery_beat",
    "debug_toolbar",
    "rest_framework_simplejwt.token_blacklist",
    # Local apps
    "apps.abstract",
    "apps.users",
    "apps.teams",
    "apps.channels",
    "apps.messages",
    "apps.assigments",
]

AUTH_USER_MODEL = "users.CustomUser"

WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

'''
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]
'''

"logging"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
        "verbose": {
            "format": "[{asctime}] {levelname} "
            "{name} {module}.{funcName}: {lineno} - {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "filename": "logs/app.log",
            "maxBytes": 5 * 1024 * 1024,  # 10 MB
            "backupCount": 3,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "debug_only": {
        "class": "logging.StreamHandler",
        "level": "DEBUG",
        "formatter": "simple",
        "filters": ["require_debug_true"],
        },
    },
    "loggers": {
        "apps.users": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps.blog": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file", "debug_only"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# ── Database (overridden per environment) ──────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": DB_ENGINE,
        "NAME": BASE_DIR / DB_NAME if DB_ENGINE.endswith("sqlite3") else DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}

# ── Password validation ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ───────────────────────────────────────────────────────
LANGUAGE_CODE = "en"  
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Добавляем поддерживаемые языки
LANGUAGES = (
    ('en', _('English')),
    ('ru', _('Russian')),
)

# Указываем, где будут лежать файлы переводов
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ── Static & Media ─────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── DRF ───────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=JWT_REFRESH_TOKEN_LIFETIME_DAYS),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── drf-spectacular ────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Teams Clone API",
    "DESCRIPTION": "API documentation for Teams Clone project",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── Logging ───────────────────────────────────────────────────────────────────


#CELERY SETTINGS
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

CEELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = "UTC"



EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CELERY_BEAT_SCHEDULE = {
    "delete-old-messages-daily": {
        "task": "apps.messages.tasks.delete_old_messages",
        "schedule": crontab(hour=0, minute=0),
    },
}
# settings/base.py

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
