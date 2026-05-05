from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import Message


class IsAuthorOrReadOnly(BasePermission):
    """
    Read access for any authenticated team member.
    Write/delete access only for the message author.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request: Request, view: APIView, obj: Message) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return obj.author_id == request.user.id
