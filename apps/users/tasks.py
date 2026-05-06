from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_welcome_email(user_id):
    from apps.users.models import CustomUser
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
