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
    UpdateAssigmentsSerializers
)
from .models import (
    Assigments,
    Assignment_Submissions
)

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

    def get_assigment_or_404(
        self, 
        pk: int
    ) -> tuple[
        Assigments | None, 
        Response | None
    ]:
        """Helper: returns (team, None) or (None, 404 Response)"""
        try:
            team = Assigments.objects.get(pk=pk)
            return team, None
        except Assigments.DoesNotExist:
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
        queryset = Assigments.objects.all().order_by('-id')
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
        team_id:None
    )->Response:
        """
        Assigments by team_id
        """
        try:
            error,assigments = self.get_assigment_or_404(team_id)

            if error:
                return error
            
            serializer = AssigmentsSerialzers(
                assigments
            )
            logger.info(
                'Assigments by team_id:%s',
                team_id
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
                team_id
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
        team_id:None
    )->Response:
        """
        Update Assigments 
        """
        assigment = self.get_assigment_or_404(team_id)

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
                team_id
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
            team_id
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
            data = request.data
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
            


