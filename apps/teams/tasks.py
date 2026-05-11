#Pyhton imports
import logging
from datetime import timedelta

#Celery imports
from celery import shared_task

#django imports
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def send_weekly_summary():
    """
    Statistics of the week:
    - number of channels
    - number of messages
    - number of members
    """
    from apps.teams.models import Team

    logger.info("Starting weekly summary task")

    teams = Team.objects.prefetch_related('members', 'channels').all()
    week_ago = timezone.now() - timedelta(days=7)

    report_lines = []
    processed_teams = 0

    for team in teams:
        num_members = team.members.count()
        num_channels = team.channels.count()

        from apps.messages.models import Message
            
        num_messages = Message.objects.filter(
            channel__team=team,
            created_at__gte=week_ago
        ).count()

        line = (
            f"Team: {team.name} | "
            f"Members: {num_members} | "
            f"Channels: {num_channels} | "
            f"Messages (last 7 days): {num_messages}"
        )
        report_lines.append(line)
        processed_teams += 1

        owner = team.owner
        subject = f"Weekly Summary for Team: {team.name}"
        body = (
            f"Hello {owner.first_name},\n\n"
            f"Here is the weekly summary for your team '{team.name}':\n\n"
            f"{line}\n\n"
            "Best regards,\n"
            "Team Management System"
        )

        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [owner.email],
                fail_silently=False,
            )
            logger.info(f"Weekly summary sent to {owner.email} for team '{team.name}'")
        except Exception as e:
            logger.error(
                f"Failed to send weekly summary to {owner.email} for team '{team.name}': {e}"
            )
    logger.info(
        f"Weekly summary task completed. Processed {processed_teams} teams."
        )
    return {
        "status": "success",
        "report": report_lines,
        "processed_teams": processed_teams
    }



