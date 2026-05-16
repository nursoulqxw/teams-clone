# Django modules
from django.apps import AppConfig


class MessagesConfig(AppConfig):
    """Application configuration for the messages app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messages"
    label = "messages_app"
