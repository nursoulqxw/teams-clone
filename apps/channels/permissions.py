# Rest modules
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

#Project modules
from apps.channels.models import Channel


class IsTeamMember(BasePermission):
    """
    Permission to check if user is a member of the team.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user is authenticated.
        Specific team membership check is done in view
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request: Request, view: APIView, obj: Channel) -> bool:
        """
        Check if user is member of the channel's team.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is member of the team
        return obj.team.members.filter(id=request.user.id).exists()
    

class IsChannelMember(BasePermission):
    """
    Permission to check if user has access to the channel.
    -Public channels: all team members have access
    -Private channels: only members have access
    """

    def has_object_permission(self, request: Request, view: APIView, obj: Channel) -> bool:
        """
        Check if user can access the channel.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        #Public channel: check team membership
        if not obj.is_private:
            return obj.team.members.filter(id=request.user.id).exists()

        # Private channel: check channel membership
        return obj.members.filter(id=request.user.id).exists()