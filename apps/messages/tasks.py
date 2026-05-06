#Python modules
import logging
from celery import shared_task
from datetime import timedelta

#Django modules
from django.core.mail import send_mail
from django.conf import settings 
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_message_notification(message_id, user_email):
    subject="New Message Notification"
    message=f"You have a new {message_id} in your channel!"
    return send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])

@shared_task
def delete_old_messages():
    from apps.messages.models import Message

    cutoff = timezone.now() - timedelta(days=30)
    old_messages = Message.objects.filter(created_at__lt=cutoff)
    count = old_messages.count()

    if count == 0:
        logger.info("delete_old_message:nothing to delete")
        return
    
    old_messages.delete()
    logger.info("delete_old_messages: deleted %d messages older than 30 days ", count)
