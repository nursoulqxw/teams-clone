#Python modules
import logging

#REST modules
from rest_framework.viewsets import ViewSet
from rest_framework.status import(
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

# drf-spectacular
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)

#Project modules
from .serializers import (
    AssigmentsSerialzers,
    CreateAssigmentsSerializers,
    UpdateAssigmentsSerializers,
    AssigmentsSubmissionsSerializers,
    CompletedAssigmentsSerializers
)
from .models import (
    Assignments,
    Assignment_Submissions
)
from .permissions import IsTeamOwner, IsTeamMember

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary='List all assignments',
        tags=['Assignments'],
        responses={
            200: OpenApiResponse(
                response=AssigmentsSerialzers(many=True),
                description='Assignments list returned successfully',
            ),
        },
    ),
    retrieve=extend_schema(
        summary='Retrieve assignments by team ID',
        tags=['Assignments'],
        responses={
            200: OpenApiResponse(response=AssigmentsSerialzers, description='Assignment found'),
            404: OpenApiResponse(description='Assignment not found'),
        },
    ),
    partial_update=extend_schema(
        summary='Update an assignment (PATCH)',
        tags=['Assignments'],
        request=UpdateAssigmentsSerializers,
        responses={
            200: OpenApiResponse(response=AssigmentsSerialzers, description='Assignment updated successfully'),
            400: OpenApiResponse(description='Validation error'),
            404: OpenApiResponse(description='Assignment not found'),
        },
    ),
    create=extend_schema(
        summary='Create an assignment',
        tags=['Assignments'],
        request=CreateAssigmentsSerializers,
        responses={
            201: OpenApiResponse(response=AssigmentsSerialzers, description='Assignment created successfully'),
            400: OpenApiResponse(description='Validation error'),
        },
    ),
)

class AssigmentsViewSet(ViewSet):
    """
    View set ASSIGMENTS
    """

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'partial_update']:
            return [IsAuthenticated(), IsTeamOwner()]
        elif self.action == 'submit_assignment':
            if self.request and self.request.method == 'GET':
                return [IsAuthenticated(), IsTeamOwner()]
            elif self.request and self.request.method == 'POST':
                return [IsAuthenticated(), IsTeamMember()]
        return super().get_permissions()

    def get_assigment_or_404(
        self, 
        pk: int
    ) -> tuple[
        Assignments | None, 
        Response | None
    ]:
        """Helper: returns (team, None) or (None, 404 Response)"""
        try:
            team = Assignments.objects.get(pk=pk)
            return team, None
        except Assignments.DoesNotExist:
            logger.warning('Team not found: id=%s', pk)
            return None, Response(
                {'error': 'Team not found.'},
                status=HTTP_404_NOT_FOUND
            )

    def list(
        self,
        request:Request,
    )->Response:
        """
        List of Assigmnets
        """
        queryset = Assignments.objects.all().order_by('-id')
        
        # Filtering by team_id if provided
        team_id = request.query_params.get('team_id')
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        
        serializer = AssigmentsSerialzers(
            queryset,
            many=True
        )
        logger.info(
            'List of assigments : %s',
            serializer.data
        )
        return Response(
            {
                'message':"List of Assigments",
                'data':serializer.data
            },
            status=HTTP_200_OK
        )
    
    def retrieve(
        self,
        request:Request,
        pk:int=None
    )->Response:
        """
        Assigments by team_id
        """
        try:
            error,assigments = self.get_assigment_or_404(pk)

            if error:
                return error
            
            serializer = AssigmentsSerialzers(
                assigments
            )
            logger.info(
                'Assigments by team_id:%s',
                pk
            )
            return Response(
                {
                'message':"Assigments by team ID",
                'data':serializer.data
                },
                status=HTTP_200_OK
            )
        except:
            logger.warning(
                'Assigments not by ID:%s',
                pk
            )
            return Response(
                {
                    'message':"not team ID"
                },
                status=HTTP_204_NO_CONTENT
            )
        
    def partial_update(
        self,
        request:Request,
        pk:int=None
    )->Response:
        """
        Update Assigments 
        """
        assigment = self.get_assigment_or_404(pk)

        serializer = UpdateAssigmentsSerializers(
            assigment,
            data = request.data,
            context = {
                'request':request
            }
        )

        if serializer.is_valid():
            assigment = serializer.save()
            logger.info(
                'Updated assigments -> assigment:%s, team_id:%s',
                assigment,
                pk
            )
            return Response(
                {
                    'message':"Updated assigments",
                    'data':AssigmentsSerialzers(assigment).data
                }
            )
        logger.error(
            'Serializer not valid: errors:%s, team_id:%s',
            serializer.errors,
            pk
        )
        return Response(
            {
                'errors':serializer.errors
            },
            status=HTTP_400_BAD_REQUEST
        )

    def create(
        self,
        request:Request
    )->Response:
        """
        Create Assigments
        """
        serializer = CreateAssigmentsSerializers(
            data = request.data,
            context = {
                'request':request
            }
        )

        if serializer.is_valid():
            
            assigment = serializer.save()

            logger.info(
                'Created assigments:%s',
                assigment
            )
            return Response(
                {
                    'message':"Created assigment",
                    'data':AssigmentsSerialzers(assigment).data
                },
                status=HTTP_201_CREATED
            )
        logger.error(
            'Serializer is not valid :%s',
            serializer.errors
        )
        return Response(
            {
                'errors':serializer.errors
            },
            status=HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        methods=['GET'],
        summary='List submissions for an assignment',
        tags=['Submissions'],
        responses={
            200: OpenApiResponse(
                response=AssigmentsSubmissionsSerializers(many=True),
                description='Submissions returned',
            ),
            404: OpenApiResponse(description='Assignment not found'),
        },
    )
    @extend_schema(
        methods=['POST'],
        summary='Submit an assignment',
        tags=['Submissions'],
        responses={
            200: OpenApiResponse(response=AssigmentsSubmissionsSerializers, description='Submitted'),
            404: OpenApiResponse(description='Assignment or submission not found'),
        },
    )
    @action(
        detail=True, 
        methods=['get', 'post'], 
        url_path='submit'
    )
    def submit_assignment(
        self, 
        request: Request, 
        pk: int = None
    ) -> Response:
        """
        GET  api/assignments/{id}/submit/ — list all submissions for this assignment
        POST api/assignments/{id}/submit/ — mark the current student's submission as submitted
        """
        error,assignment= self.get_assigment_or_404(pk)
        if error:
            return error

        if request.method == 'GET':
            return self._list_submissions(request, assignment)

        if request.method == 'POST':
            return self._submit(request, assignment)

    def _list_submissions(
        self,
        request: Request,
        assignment: Assignments,
    ) -> Response:
        """Return all submissions for a given assignment."""
        submissions = Assignment_Submissions.objects.filter(
            assignment=assignment
        ).select_related('student')

        serializer = AssigmentsSubmissionsSerializers(submissions, many=True)
        logger.info(
            'Submissions listed: assignment_id=%s by user=%s',
            assignment.id,
            request.user.id,
        )
        return Response(
            {
                'message': 'Submissions list',
                'count': submissions.count(),
                'data': serializer.data,
            },
            status=HTTP_200_OK,
        )

    def _submit(
        self,
        request: Request,
        assignment: Assignments,
    ) -> Response:
        """Mark the requesting student's submission as submitted and update status."""
        try:
            submission = Assignment_Submissions.objects.get(
                assignment=assignment,
                student=request.user,
            )
        except Assignment_Submissions.DoesNotExist:
            logger.warning(
                'Submission not found: assignment_id=%s user=%s',
                assignment.id,
                request.user.id,
            )
            return Response(
                {'error': 'Submission record not found for this user.'},
                status=HTTP_404_NOT_FOUND,
            )

        submission.submitted = True

        serializer = CompletedAssigmentsSerializers(
            submission,
            data={},        
            partial=True,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=HTTP_400_BAD_REQUEST)

        submission = serializer.save()
        logger.info(
            'Assignment submitted: id=%s status=%s by user=%s',
            assignment.id,
            submission.status,
            request.user.id,
        )
        return Response(
            {
                'message': 'Assignment submitted successfully',
                'data': AssigmentsSubmissionsSerializers(submission).data,
            },
            status=HTTP_200_OK,
        )
    
        


