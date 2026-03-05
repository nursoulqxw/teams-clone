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

# drf-spectacular
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes

from .permissions import IsTeamOwnerOrAdmin, IsTeamMember

# Project modules
from .serializers import (
    TeamSerializer,
    CreateTeamSerializer,
    UpdateTeamSerializer,
    TeamMembershipSerializer,
    CreateTeamMembershipSerializer,
)
from apps.assigments.serializers import (
    AssigmentsSerialzers,
    CreateAssigmentsSerializers
)
from .models import Team, TeamMembership
from apps.assigments.models import Assigments
from .permissions import (
    IsTeamOwnerOrAdmin,
    IsTeamMember
)
from .filters import build_team_q,build_membership_q

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary='List all teams',
        description='Supports filtering.',
        tags=['Teams'],
        responses={
            200: OpenApiResponse(
                response=TeamSerializer(many=True),
                description='Teams list returned successfully',
            )
        },
    ),
    retrieve=extend_schema(
        summary='Retrieve a team',
        tags=['Teams'],
        responses={
            200: OpenApiResponse(response=TeamSerializer, description='Team found'),
            404: OpenApiResponse(description='Team not found'),
        },
    ),
    create=extend_schema(
        summary='Create a team',
        tags=['Teams'],
        request=CreateTeamSerializer,
        responses={
            201: OpenApiResponse(response=TeamSerializer, description='Team created successfully'),
            400: OpenApiResponse(description='Validation error'),
        },
    ),
    partial_update=extend_schema(
        summary='Update a team (PATCH)',
        tags=['Teams'],
        request=UpdateTeamSerializer,
        responses={
            200: OpenApiResponse(response=TeamSerializer, description='Team updated successfully'),
            400: OpenApiResponse(description='Validation error'),
            404: OpenApiResponse(description='Team not found'),
        },
    ),
    destroy=extend_schema(
        summary='Delete a team',
        tags=['Teams'],
        responses={
            204: OpenApiResponse(description='Team deleted successfully'),
            404: OpenApiResponse(description='Team not found'),
        },
    ),
)


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
    

    def get_permissions(self):
        """Return permission instances based on action and HTTP method."""
        # default: authenticated users
        permission_classes = [IsAuthenticated]

        # update and delete require owner or admin
        if self.action in ['partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsTeamOwnerOrAdmin]

        # members endpoint: GET -> team members, POST/DELETE -> owner/admin
        if self.action == 'members':
            if getattr(self, 'request', None) and self.request.method == 'GET':
                permission_classes = [IsAuthenticated, IsTeamMember]
            else:
                permission_classes = [IsAuthenticated, IsTeamOwnerOrAdmin]

        return [permission() for permission in permission_classes]

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

        conds = build_team_q(request)
        queryset = Team.objects.filter(conds).order_by('id').distinct()

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


    @extend_schema(
        methods=['GET'],
        summary='List team members',
        tags=['Team Members'],
        responses={
            200: OpenApiResponse(
                response=TeamMembershipSerializer(many=True),
                description='Members list returned successfully',
            ),
            404: OpenApiResponse(description='Team not found'),
        },
    )
    @extend_schema(
        methods=['POST'],
        summary='Add a member to a team',
        tags=['Team Members'],
        request=CreateTeamMembershipSerializer,
        responses={
            201: OpenApiResponse(response=TeamMembershipSerializer, description='Member added successfully'),
            400: OpenApiResponse(description='Validation error'),
            404: OpenApiResponse(description='Team not found'),
        },
    )
    @extend_schema(
        methods=['DELETE'],
        summary='Remove a member from a team',
        tags=['Team Members'],
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                'Delete member example',
                value={'user_id': 1},
                request_only=True,
            )
        ],
        responses={
            204: OpenApiResponse(description='Member removed successfully'),
            400: OpenApiResponse(description='user_id is required'),
            404: OpenApiResponse(description='Team or member not found'),
        },
    )

    @action(
        detail=True,
        methods=['get','post'],
        url_path='assigment'
    )
    def assigments(
        self,
        request:Request,
        pk:int = None
    )->Response:
        """
        Assigment by team and team_id
        """
        team,error = self.get_team_or_404(pk)
        if error:
            return error

        if request.method == 'GET':
            logger.info('list of assigments by team_id:%s',team)
            return self._list_assigments(request,team)
        
        if request.method == "POST":
            logger.info('Create assigment by team and team_id: %s',team)
            return self._create_assigments(request,team)
        
    def _list_assigments(
        self,
        request:Request,
        team:int=None
    )->Response:
        """
        List assigments
        """
        assigment = Assigments.objects.filter(
            team = team
        ).order_by('due_data')

        serializer = AssigmentsSerialzers(
            assigment,
            many = True
        )

        logger.info(
            'List assigments by team and team_id: %s,assigment:%s',
            team,
            assigment
        )

        return Response(
            {
                'meassage':"Assigments by team_id",
                'data':serializer.data
            },
            status = HTTP_200_OK
        )
    
    def _create_assignment(
        self,
        request: Request,
        team: Team
    ) -> Response:
        """Create an assignment for a team."""
        serializer = CreateAssigmentsSerializers(
            data=request.data,
            context={'request': request, 'team': team}
        )
        if not serializer.is_valid():
            logger.warning(
                'Assignment creation failed: team_id=%s errors=%s',
                team.id,
                serializer.errors
            )
            return Response(
                {'error': serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )

        assignment = serializer.save(team=team)
        logger.info(
            'Assignment created: id=%s team_id=%s by user=%s',
            assignment.id,
            team.id,
            request.user.id
        )
        return Response(
            {
                'message': 'Assignment created successfully',
                'data': AssigmentsSerialzers(assignment).data,
            },
            status=HTTP_201_CREATED,
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

        filtering = build_membership_q(request,team)
        memberships = TeamMembership.objects.filter(
            filtering
        ).select_related(
            'user'
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
        } 
        serializer = CreateTeamMembershipSerializer(
            data=data,  
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