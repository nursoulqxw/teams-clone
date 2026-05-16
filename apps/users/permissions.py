# DRF modules
from rest_framework.permissions import BasePermission, SAFE_METHODS

# Project modules
from apps.users.models import CustomUser


class IsOwnerOrAdmin(BasePermission):
    """Custom permission to only allow owners or admins to edit objects."""

    def has_permission(self, request: object, view: object) -> bool:
        """Allow access only to authenticated users."""
        return request.user and request.user.is_authenticated

    def has_object_permission(
        self,
        request: object,
        view: object,
        obj: CustomUser,
    ) -> bool:
        """Allow read-only for safe methods, write only for owner or admin."""
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_staff
            or request.user.is_superuser
            or obj == request.user
        )
