from rest_framework.permissions import BasePermission
from .models import Assignments
from apps.team.models import Team


class IsTeamOwner(BasePermission):
    """
    Custom permission to only allow team owners to access certain views.
    """

    def has_permission(self, request, view):
        if view.action == 'create':
            team_id = request.data.get('team_id')
            if team_id:
                try:
                    team = Team.objects.get(id=team_id)
                    return team.owner == request.user
                except Team.DoesNotExist:
                    return False
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Assignments):
            return obj.team_id.owner == request.user
        return False


class IsTeamMember(BasePermission):
    """
    Custom permission to only allow team members to access certain views.
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Assignments):
            return obj.team_id.members.filter(id=request.user.id).exists()
        return False