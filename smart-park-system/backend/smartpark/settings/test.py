import sys
from .base import *

# Test database
if "test" in sys.argv or "pytest" in sys.modules:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }


# Disable migrations during tests for speed
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


# Only use migrations disable if not testing migrations specifically
if not any(arg in sys.argv for arg in ["makemigrations", "migrate", "showmigrations"]):
    MIGRATION_MODULES = DisableMigrations()

# Fast password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disable email sending
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Static files configuration for tests
STATIC_URL = "/static/"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Logging configuration for tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}

# Test specific settings
TEST_RUNNER = "django.test.runner.DiscoverRunner"
DEBUG = False
TEMPLATE_DEBUG = False

# Security settings for tests
SECRET_KEY = "test-secret-key-only-for-ci-cd-pipeline"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# CORS settings for tests
CORS_ALLOW_ALL_ORIGINS = True

# JWT settings for tests (shorter expiry for faster testing)
SIMPLE_JWT.update(
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
        "REFRESH_TOKEN_LIFETIME": timedelta(minutes=10),
    }
)
