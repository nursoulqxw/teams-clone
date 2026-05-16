# Django REST Framework
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView

# Project modules
from .models import Message


class IsAuthorOrReadOnly(BasePermission):
    """
    Read access for any authenticated team member.
    Write/delete access only for the message author.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Allows access only to authenticated users."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: Message,
    ) -> bool:
        """Allows safe methods for all; mutating methods only for author/staff."""
        if request.method in SAFE_METHODS:
            return True
        return (
            obj.author_id == request.user.id
            or request.user.is_staff
            or request.user.is_superuser
        )
