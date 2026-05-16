# Python modules
import logging
from datetime import timedelta

# Celery modules
from celery import shared_task

# Django modules
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

MESSAGE_RETENTION_DAYS = 30


@shared_task
def send_message_notification(message_id: int, user_email: str) -> int:
    """Sends an email notification to the user about a new message."""
    subject: str = "New Message Notification"
    message: str = f"You have a new message (id={message_id}) in your channel!"
    return send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])


@shared_task
def delete_old_messages() -> None:
    """Deletes all messages older than 30 days."""
    from apps.messages.models import Message

    cutoff = timezone.now() - timedelta(days=MESSAGE_RETENTION_DAYS)
    old_messages = Message.objects.filter(created_at__lt=cutoff)
    count: int = old_messages.count()

    if count == 0:
        logger.info("delete_old_messages: nothing to delete.")
        return

    old_messages.delete()
    logger.info(
        "delete_old_messages: deleted %d messages older than %d days.",
        count,
        MESSAGE_RETENTION_DAYS,
    )
