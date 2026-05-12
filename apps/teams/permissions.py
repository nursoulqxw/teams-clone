import logging

from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Team, TeamMembership

logger = logging.getLogger(__name__)


class IsTeamOwner(BasePermission):
    """
    Allow access only to the team's owner.
    Applied to: PATCH (update) and DELETE (destroy) team endpoints.
    """

    message = "Only the team owner can perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user

        if user.is_staff or user.is_superuser:
            return True

        team = obj if isinstance(obj, Team) else getattr(obj, "team", None)
        if team is None:
            logger.warning(
                "IsTeamOwner: could not resolve team from obj=%s",
                type(obj).__name__,
            )
            return False

        is_owner = team.owner_id == user.id
        if not is_owner:
            logger.warning(
                "IsTeamOwner denied: user=%s is not owner of team=%s (owner=%s)",
                user.id,
                team.id,
                team.owner_id,
            )
        return is_owner


class IsTeamMemberOrOwner(BasePermission):
    """
    Allow access to team members AND the team owner.

    Applied to: retrieve team details, list channels/messages inside a team.

    - Safe methods (GET, HEAD, OPTIONS): any authenticated user can call
      view-level check; object-level enforces team membership.
    - Write methods: delegates to IsTeamOwner logic (owner or admin).
    """

    message = "You must be a member or owner of this team to access it."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user

        if user.is_staff or user.is_superuser:
            return True

        team = obj if isinstance(obj, Team) else getattr(obj, "team", None)
        if team is None:
            logger.warning(
                "IsTeamMemberOrOwner: could not resolve team from obj=%s",
                type(obj).__name__,
            )
            return False

        if team.owner_id == user.id:
            return True

        # Check membership table
        is_member = TeamMembership.objects.filter(team=team, user=user).exists()
        if not is_member:
            logger.warning(
                "IsTeamMemberOrOwner denied: user=%s is neither owner nor member of team=%s",
                user.id,
                team.id,
            )
        return is_member


class CanManageTeamMembers(BasePermission):
    """
    Allow adding / removing team members only to:
      - the team owner, OR
      - a team admin (role='admin' in TeamMembership)
    Applied to: POST/DELETE /api/teams/{id}/members/
    """

    message = "Only the team owner or an admin can manage team members."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user

        if request.method in SAFE_METHODS:
            return True

        if user.is_staff or user.is_superuser:
            return True

        team = obj if isinstance(obj, Team) else getattr(obj, "team", None)
        if team is None:
            logger.warning(
                "CanManageTeamMembers: could not resolve team from obj=%s",
                type(obj).__name__,
            )
            return False

        if team.owner_id == user.id:
            return True

        is_admin = TeamMembership.objects.filter(
            team=team, user=user, role="admin"
        ).exists()
        if not is_admin:
            logger.warning(
                "CanManageTeamMembers denied: user=%s is not owner/admin of team=%s",
                user.id,
                team.id,
            )
        return is_admin


class IsTeamOwnerOrAdmin(CanManageTeamMembers):
    """Alias kept for backward compatibility with existing views."""


class IsTeamMember(IsTeamMemberOrOwner):
    """Alias kept for backward compatibility with existing views."""