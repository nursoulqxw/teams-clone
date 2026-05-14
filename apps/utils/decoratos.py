# Python imports
import logging
import functools
import hashlib

#django imports
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

# rest imports
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND
)

#project imports
from apps.teams.models import Team

logger = logging.getLogger(__name__)


def call_log_api(func):
    """
    Call logging decorator to log API calls with user and request data.
    """

    @functools.wraps(func)
    def wrapper(view_instance, request, *args, **kwargs):

        user = request.user
        user_info = (
            f"User: {user.first_name} {user.last_name} (ID: {user.id}, Email: {user.email})"
            if user and user.is_authenticated
            else "Unauthenticated User"
        )

        view_name = type(view_instance).__name__
        method = request.method
        action = getattr(view_instance, "action", None)
        endpoint = f"{view_name}.{action or func.__name__}"

        logger.info(
            "[API CALL START] %s - %s - Endpoint: %s",
            user_info,
            method,
            endpoint
        )

        response = func(view_instance, request, *args, **kwargs)

        status_code = response.status_code if isinstance(response, Response) else "N/A"

        logger.info(
            "[API CALL END] %s - %s - Endpoint: %s - Status Code: %s",
            user_info,
            method,
            endpoint,
            status_code
        )

        return response
    
    return wrapper

def require_team_member(team_lookup: str = "pk"):
    """
    Require team members
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(view_instance, request, *args, **kwargs):

            team_id = kwargs.get(team_lookup)

            if team_id is None:
                logging.error(
                    'team id is not correctly passed in the url, expected "%s" but got "%s"',
                    team_lookup,
                    team_id
                )
                return Response(
                    {"detail": _("Team ID is required.")},
                    status=HTTP_404_NOT_FOUND
                )
            
            try:
                team = Team.objects.get(pk=team_id)
            
            except Team.DoesNotExist:
                logging.warning(
                    'team with id "%s" does not exist',
                    team_id
                )
                return Response(
                    {"detail": _("Team not found.")},
                    status=HTTP_404_NOT_FOUND
                )
            
            user = request.user

            is_owner = team.owner_id == user.id
            is_member = team.members.filter(id=user.id).exists()

            if not (is_owner or is_member):
                logging.warning(
                    'user "%s" is not a member of team "%s"',
                    user.email,
                    team.name
                )
                return Response(
                    {"detail": _("You do not have permission to access this team.")},
                    status=HTTP_403_FORBIDDEN
                )
            
            view_instance.team = team

            logging.debug(
                'user "%s" is accessing team "%s"',
                user.email,
                team.name
            )

            return func(view_instance, request, *args, **kwargs)
        
        return wrapper
    
    return decorator

