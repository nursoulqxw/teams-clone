from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission to only allow owners or admins to edit objects.
    Read-only access is allowed for any request.
    """
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user.is_superuser or obj == request.user
    
