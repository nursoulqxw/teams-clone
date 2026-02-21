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
    #permission_classes = [IsAuthenticated]

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
        logger.info(
            'Team created: id=%s by user=%s', 
            team.id, 
            request.user.id
        )
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
        logger.info(
            'Team updated: id=%s by user=%s', 
            team.id, 
            request.user.id
        )
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
        logger.info(
            'Team deleted: id=%s by user=%s', 
            team_id, 
            request.user.id
        )
        return Response(
            {'message': 'Team deleted successfully'},
            status=HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True, 
        methods=['get', 'post','delete'], 
        url_path='members'
    )
    def members(self, request: Request, pk: int = None) -> Response:
        """
        GET    api/teams/{id}/members/ — list members
        POST   api/teams/{id}/members/ — add member
        DELETE api/teams/{id}/members/ — delete member
        """
        team, error = self.get_team_or_404(pk=pk)
        if error:
            return error

        if request.method == 'GET':
            logger.info('List of members: team=%s', team.id)
            return self._list_members(request, team)

        if request.method == 'POST':
            logger.info('Adding member: team=%s', team.id)
            return self._add_members(request, team)

        if request.method == 'DELETE':
            logger.info('Deleting member: team=%s', team.id)
            return self._delete_members(request, team)


    def _list_members(
        self, 
        request: Request, 
        team: Team
    ) -> Response:
        """List of members"""
        memberships = TeamMembership.objects.filter(
            team=team
        ).prefetch_related(
            'members'
        )
        serializer = TeamMembershipSerializer(
            memberships, 
            many=True
        )
        logger.info(
            'Listed members: team=%s count=%s', 
            team.id, memberships.count()
        )
        return Response(
            {
                'message': 'List of members',
                'count': memberships.count(),
                'data': serializer.data,
            },
            status=HTTP_200_OK,
        )


    def _add_members(
        self, 
        request: Request, 
        team: Team
    ) -> Response:
        """Add member to team"""
        data = {
            **request.data, 
            'team': team.id
        }  # добавляем team в data
        serializer = CreateTeamMembershipSerializer(
            data=data,  # передаём data с team
            context={'request': request}
        )
        if not serializer.is_valid():
            logger.warning(
                'Add member failed: team=%s errors=%s',
                team.id,
                serializer.errors
            )
            return Response(
                {'error': serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )

        membership = serializer.save()
        logger.info(
            'Member added: team=%s membership=%s role=%s',
            team.id,
            membership.id,
            membership.role
        )
        return Response(
            {
                'message': 'Member added successfully',
                'data': TeamMembershipSerializer(membership).data,
            },
            status=HTTP_201_CREATED,
        )


    def _delete_members(
        self, 
        request: Request, 
        team: Team
    ) -> Response:
        """Delete member from team"""
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=HTTP_400_BAD_REQUEST,
            )

        membership = TeamMembership.objects.filter(
            team=team, user_id=user_id
        ).first()

        if not membership:
            return Response(
                {'error': 'Member not found in this team'},
                status=HTTP_404_NOT_FOUND,
            )

        membership.delete()
        logger.info('Member deleted: team=%s user=%s', team.id, user_id)
        return Response(
            {'message': 'Member deleted successfully'},
            status=HTTP_204_NO_CONTENT,
        )