#django imports
from django.core.mail import send_mail
from django.conf import settings

#celery imports
from celery import shared_task

#project imports
from .models import CustomUser


@shared_task
def send_welcome_email(user_id):

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return

    send_mail(
        subject="Welcome to Teams Clone!",
        message=f"Hi {user.first_name}, your account is ready.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
