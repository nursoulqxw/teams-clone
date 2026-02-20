# Python modules
import logging

# Rest modules
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_204_NO_CONTENT,
)
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

# Project modules
from .serializers import (
    TeamSerializer,
    CreateTeamSerializer,
    UpdateTeamSerializer,
    TeamMembershipSerializer,
    CreateTeamMembershipSerializer,
    UpdateTeamMembershipSerializer,
)
from .models import Team, TeamMembership

logger = logging.getLogger(__name__)


class TeamViewSet(ViewSet):
    """
    Team endpoints:
        GET    api/teams/              - list all teams
        POST   api/teams/              - create team
        GET    api/teams/{id}/         - retrieve team
        PATCH  api/teams/{id}/         - update team
        DELETE api/teams/{id}/         - delete team
        GET    api/teams/{id}/members/ - list members of team
        POST   api/teams/{id}/members/ - add member to team
    """
    permission_classes = [IsAuthenticated]

    def get_team_or_404(
        self, 
        pk: int
    ) -> tuple[Team | None, Response | None]:
        """Helper: returns (team, None) or (None, 404 Response)"""
        try:
            team = Team.objects.get(pk=pk)
            return team, None
        except Team.DoesNotExist:
            logger.warning('Team not found: id=%s', pk)
            return None, Response(
                {'error': 'Team not found.'},
                status=HTTP_404_NOT_FOUND
            )

    def list(
        self, 
        request: Request
    ) -> Response:
        """GET api/teams/ — list all teams"""
        queryset = Team.objects.all().order_by('id')
        serializer = TeamSerializer(queryset, many=True)
        logger.debug('Team list requested by user: %s', request.user.id)
        return Response(
            {
                'message': 'List of teams',
                'count': queryset.count(),
                'data': serializer.data,
            },
            status=HTTP_200_OK,
        )

    def retrieve(
        self, 
        request: Request, 
        pk: int = None
    ) -> Response:
        """GET api/teams/{id}/ — retrieve one team"""
        team, error = self.get_team_or_404(pk)
        if error:
            return error

        serializer = TeamSerializer(team)
        logger.info('Team retrieved: id=%s by user=%s', pk, request.user.id)
        return Response(
            {
                'message': 'Team detail',
                'data': serializer.data,
            },
            status=HTTP_200_OK,
        )

    def create(
        self, 
        request: Request
    ) -> Response:
        """POST api/teams/ — create a team"""
        serializer = CreateTeamSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            logger.warning(
                'Team creation failed: user=%s errors=%s',
                request.user.id,
                serializer.errors
            )
            return Response(
                {'error': serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )

        team = serializer.save()
        logger.info('Team created: id=%s by user=%s', team.id, request.user.id)
        return Response(
            {
                'message': 'Team created successfully',
                'data': TeamSerializer(team).data,  # возвращаем полный read serializer
            },
            status=HTTP_201_CREATED,
        )

    def partial_update(
        self, 
        request: Request, 
        pk: int = None
    ) -> Response:
        """PATCH api/teams/{id}/ — update team"""
        team, error = self.get_team_or_404(pk)
        if error:
            return error

        serializer = UpdateTeamSerializer(
            team,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if not serializer.is_valid():
            logger.warning(
                'Team update failed: id=%s errors=%s',
                pk,
                serializer.errors
            )
            return Response(
                {'error': serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )

        team = serializer.save()
        logger.info('Team updated: id=%s by user=%s', team.id, request.user.id)
        return Response(
            {
                'message': 'Team updated successfully',
                'data': TeamSerializer(team).data,
            },
            status=HTTP_200_OK,
        )

    def destroy(
        self, 
        request: Request, 
        pk: int = None
    ) -> Response:
        """DELETE api/teams/{id}/ — delete team"""
        team, error = self.get_team_or_404(pk)
        if error:
            return error

        team_id = team.id
        team.delete()
        logger.info('Team deleted: id=%s by user=%s', team_id, request.user.id)
        return Response(
            {'message': 'Team deleted successfully'},
            status=HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True, 
        methods=['get', 'post'], 
        url_path='members'
    )
    def members(
        self, 
        request: Request, 
        pk: int = None
    ) -> Response:
        """
        GET  api/teams/{id}/members/ — list members
        POST api/teams/{id}/members/ — add member
        """
        team, error = self.get_team_or_404(pk)
        if error:
            return error

        if request.method == 'GET':
            return self._list_members(request, team)
        if request.method == 'POST':
            return self._add_member(request, team)
        