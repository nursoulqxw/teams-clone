from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Team, TeamMembership


class IsTeamOwnerOrAdmin(BasePermission):
	"""Allow access only to team owner, team admins, or staff/superusers.

	Safe methods are allowed for any request.
	Object may be a `Team` or a model with a `team` attribute (e.g. TeamMembership).
	"""

	def has_object_permission(self, request, view, obj):
		user = request.user

		if request.method in SAFE_METHODS:
			return True

		if user.is_staff or user.is_superuser:
			return True

		# resolve team for object
		if isinstance(obj, Team):
			team = obj
		elif hasattr(obj, 'team'):
			team = getattr(obj, 'team')
		else:
			return False

		if team.owner == user:
			return True

		return TeamMembership.objects.filter(
			team=team, 
			user=user, 
			role='admin').exists()


class IsTeamMember(BasePermission):
	"""Allow access to team members and owners (and staff/superusers).

	Safe methods are allowed for any request.
	"""

	def has_object_permission(self, request, view, obj):
		user = request.user

		if request.method in SAFE_METHODS:
			return True

		if user.is_staff or user.is_superuser:
			return True

		if isinstance(obj, Team):
			team = obj
		elif hasattr(obj, 'team'):
			team = getattr(obj, 'team')
		else:
			return False

		if team.owner == user:
			return True

		return TeamMembership.objects.filter(
			team=team,  
			user=user).exists()


