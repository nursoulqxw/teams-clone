#python imports
import logging
from typing import Tuple

#django imports
from django.utils.translation import gettext_lazy as _

#rest imports
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND
)

#project imports
from apps.teams.models import Team
 
logger = logging.getLogger(__name__)


class TeamAccessMixin:
    """
    Mixin to check if the user is a member of the team before allowing access to the view.
    """

    def _fetch_team(self, pk):
        
        try:
            return Team.objects.get(pk=pk)
        except (Team.DoesNotExist, ValueError, TypeError):
            return None
 
    # ── get_team_or_404 ───────────────────────────────────────────────────────
    def get_team_or_404(self, pk) -> Tuple:
        """
        Team id 
          (team, None)        
          (None, Response404)
        """

        team = self._fetch_team(pk)

        if team is None:
            logger.warning(
                "TeamAccessMixin.get_team_or_404: team_id=%s табылмады.",
                pk
            )

            return None, Response(
                {"error": _("Команда табылмады.")},
                status=HTTP_404_NOT_FOUND,
            )
        
        return team, None
 
    # ── get_team_or_403 ───────────────────────────────────────────────────────
    def get_team_or_403(self, pk) -> Tuple:
        
        team = self._fetch_team(pk)

        if team is None:

            logger.warning(
                "TeamAccessMixin.get_team_or_403: team_id=%s табылмады (403 қайтарылды).", pk
            )

            return None, Response(
                {"error": _("Бұл ресурсқа қол жеткізуге рұқсатыңыз жоқ.")},
                status=HTTP_403_FORBIDDEN,
            )
        
        return team, None
 
    # ── check_team_membership ─────────────────────────────────────────────────
    def check_team_membership(self, team, user) -> bool:
        
        if not user or not user.is_authenticated:
            return False
 
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True
 
        if team.owner_id == user.id:
            return True
 
        return team.members.filter(id=user.id).exists()
 
    # ── assert_team_member ────────────────────────────────────────────────────
    def assert_team_member(self, team, user):
        
        if not self.check_team_membership(team, user):

            logger.warning(
                "TeamAccessMixin.assert_team_member: user_id=%s team_id=%s — қол жеткізу тосқауылданды.",
                getattr(user, "id", "?"),
                team.id,
            )

            return Response(
                {"error": _("Сіз бұл команданың мүшесі емессіз.")},
                status=HTTP_403_FORBIDDEN,
            )
        
        return None
 
    # ── assert_team_owner ─────────────────────────────────────────────────────
    def assert_team_owner(self, team, user):
        
        is_owner = (team.owner_id == user.id)

        is_super = getattr(user, "is_superuser", False) or getattr(user, "is_staff", False)
 
        if not (is_owner or is_super):

            logger.warning(
                "TeamAccessMixin.assert_team_owner: user_id=%s team_id=%s — иесі емес.",
                getattr(user, "id", "?"),
                team.id,
            )

            return Response(
                {"error": _("Тек команда иесі бұл әрекетті орындай алады.")},
                status=HTTP_403_FORBIDDEN,
            )
        
        return None


class LoggingMixin:
    """
    Mixin to add logging functionality to views.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
 
        #meta data for logging
        user        = request.user
        user_info   = (
            f"user_id={user.id} ({user.email})"
            if user and user.is_authenticated
            else "anonymous"
        )

        action      = getattr(self, "action", None) or request.method
        method      = request.method
        path        = request.path
        status_code = getattr(response, "status_code", "?")
        view_name   = type(self).__name__
 
        #log level 
        if isinstance(status_code, int):

            if status_code >= 500:
                log_level = logging.ERROR

            elif status_code >= 400:
                log_level = logging.WARNING

            else:
                log_level = logging.INFO

        else:
            log_level = logging.DEBUG
 
        logger.log(
            log_level,
            "[%s] %s | %s %s → HTTP %s | %s",
            view_name,
            user_info,
            method,
            path,
            status_code,
            action,
        )
 
        return response
 
    #Starting action logging at the beginning of the request processing
    def initial(self, request, *args, **kwargs):
        
        super().initial(request, *args, **kwargs)
 
        user      = request.user
        user_info = (
            f"user_id={user.id}"
            if user and user.is_authenticated
            else "anonymous"
        )

        action    = getattr(self, "action", None) or request.method
        view_name = type(self).__name__
 
        logger.debug(
            "[%s] REQUEST START | %s | %s %s | action=%s",
            view_name,
            user_info,
            request.method,
            request.path,
            action,
        )
 
