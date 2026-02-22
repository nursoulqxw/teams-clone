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
    ChannelSerializer,
    CreateChannelSerializer,
    UpdateChannelSerializer,
    ChannelMembershipSerializer,
    AddChannelMemberSerializer,
)
from .models import Channel, ChannelMembership
from .permissions import IsTeamMember, IsChannelMember

logger = logging.getLogger(__name__)


class ChannelViewSet(ViewSet):
    """
    Channel endpoints:
        GET    /api/channels/?team_id={id}  - list channels in team
        POST   /api/channels/               - create channel
        GET    /api/channels/{id}/          - retrieve channel
        PATCH  /api/channels/{id}/          - update channel
        DELETE /api/channels/{id}/          - delete channel
        GET    /api/channels/{id}/members/  - list members (private only)
        POST   /api/channels/{id}/members/  - add member (private only)
        DELETE /api/channels/{id}/members/  - remove member (private only)
    """
    
    permission_classes = [IsAuthenticated, IsTeamMember]
    
    def get_channel_or_404(self, pk: int) -> tuple[Channel | None, Response | None]:
        """Helper: returns (channel, None) or (None, 404 Response)"""
        try:
            channel = Channel.objects.select_related('team').get(pk=pk)
            return channel, None
        except Channel.DoesNotExist:
            logger.warning('Channel not found: id=%s', pk)
            return None, Response(
                {'error': 'Channel not found.'},
                status=HTTP_404_NOT_FOUND
            )
    
    def list(self, request: Request) -> Response:
        """
        GET /api/channels/?team_id={id}
        List all channels in a team.
        Required query parameter: team_id
        """
        team_id = request.query_params.get('team_id')
        
        if not team_id:
            return Response(
                {'error': 'team_id query parameter is required.'},
                status=HTTP_400_BAD_REQUEST
            )
        
        try:
            team_id = int(team_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'team_id must be a valid integer.'},
                status=HTTP_400_BAD_REQUEST
            )
        
        # Get channels - public ones + private ones where user is member
        queryset = Channel.objects.filter(team_id=team_id).select_related('team')
        
        # Filter: show public channels OR private channels where user is member
        user = request.user
        public_channels = queryset.filter(is_private=False)
        private_channels = queryset.filter(
            is_private=True,
            members=user
        )
        
        all_channels = (public_channels | private_channels).distinct().order_by('name')
        
        serializer = ChannelSerializer(all_channels, many=True)
        
        logger.info(
            'Channels listed: team=%s user=%s count=%s',
            team_id,
            user.id,
            all_channels.count()
        )
        
        return Response(
            {
                'message': 'List of channels',
                'count': all_channels.count(),
                'data': serializer.data,
            },
            status=HTTP_200_OK
        )
    
    def retrieve(self, request: Request, pk: int = None) -> Response:
        """
        GET /api/channels/{id}/
        Retrieve one channel.
        """
        channel, error = self.get_channel_or_404(pk)
        if error:
            return error
        
        # Check permission: public OR user is member
        if channel.is_private:
            if not channel.members.filter(id=request.user.id).exists():
                return Response(
                    {'error': 'You do not have access to this private channel.'},
                    status=HTTP_404_NOT_FOUND
                )
        
        serializer = ChannelSerializer(channel)
        
        logger.info(
            'Channel retrieved: id=%s by user=%s',
            pk,
            request.user.id
        )
        
        return Response(
            {
                'message': 'Channel detail',
                'data': serializer.data,
            },
            status=HTTP_200_OK
        )
    
    def create(self, request: Request) -> Response:
        """
        POST /api/channels/
        Create a channel.
        """
        serializer = CreateChannelSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            logger.warning(
                'Channel creation failed: user=%s errors=%s',
                request.user.id,
                serializer.errors
            )
            return Response(
                {'error': serializer.errors},
                status=HTTP_400_BAD_REQUEST
            )
        
        channel = serializer.save()
        
        logger.info(
            'Channel created: id=%s name=%s team=%s by user=%s',
            channel.id,
            channel.name,
            channel.team.id,
            request.user.id
        )
        
        return Response(
            {
                'message': 'Channel created successfully',
                'data': ChannelSerializer(channel).data,
            },
            status=HTTP_201_CREATED
        )
    
    def partial_update(self, request: Request, pk: int = None) -> Response:
        """
        PATCH /api/channels/{id}/
        Update a channel.
        """
        channel, error = self.get_channel_or_404(pk)
        if error:
            return error
        
        serializer = UpdateChannelSerializer(
            channel,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            logger.warning(
                'Channel update failed: id=%s errors=%s',
                pk,
                serializer.errors
            )
            return Response(
                {'error': serializer.errors},
                status=HTTP_400_BAD_REQUEST
            )
        
        channel = serializer.save()
        
        logger.info(
            'Channel updated: id=%s by user=%s',
            channel.id,
            request.user.id
        )
        
        return Response(
            {
                'message': 'Channel updated successfully',
                'data': ChannelSerializer(channel).data,
            },
            status=HTTP_200_OK
        )
    
    def destroy(self, request: Request, pk: int = None) -> Response:
        """
        DELETE /api/channels/{id}/
        Delete a channel.
        """
        channel, error = self.get_channel_or_404(pk)
        if error:
            return error
        
        channel_id = channel.id
        channel_name = channel.name
        channel.delete()
        
        logger.info(
            'Channel deleted: id=%s name=%s by user=%s',
            channel_id,
            channel_name,
            request.user.id
        )
        
        return Response(
            {'message': 'Channel deleted successfully'},
            status=HTTP_204_NO_CONTENT
        )
    
    @action(
        detail=True,
        methods=['get', 'post', 'delete'],
        url_path='members'
    )
    def members(self, request: Request, pk: int = None) -> Response:
        """
        GET    /api/channels/{id}/members/ - list members
        POST   /api/channels/{id}/members/ - add member
        DELETE /api/channels/{id}/members/ - remove member
        
        Only for private channels.
        """
        channel, error = self.get_channel_or_404(pk)
        if error:
            return error
        
        # Check if channel is private
        if not channel.is_private:
            return Response(
                {'error': 'This endpoint is only for private channels.'},
                status=HTTP_400_BAD_REQUEST
            )
        
        if request.method == 'GET':
            return self._list_members(request, channel)
        elif request.method == 'POST':
            return self._add_member(request, channel)
        elif request.method == 'DELETE':
            return self._remove_member(request, channel)
    
    def _list_members(self, request: Request, channel: Channel) -> Response:
        """List members of private channel."""
        memberships = ChannelMembership.objects.filter(
            channel=channel
        ).select_related('user')
        
        serializer = ChannelMembershipSerializer(memberships, many=True)
        
        logger.info(
            'Listed channel members: channel=%s count=%s',
            channel.id,
            memberships.count()
        )
        
        return Response(
            {
                'message': 'List of channel members',
                'count': memberships.count(),
                'data': serializer.data,
            },
            status=HTTP_200_OK
        )
    
    def _add_member(self, request: Request, channel: Channel) -> Response:
        """Add member to private channel."""
        data = {
            **request.data,
            'channel': channel.id
        }
        
        serializer = AddChannelMemberSerializer(
            data=data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            logger.warning(
                'Add channel member failed: channel=%s errors=%s',
                channel.id,
                serializer.errors
            )
            return Response(
                {'error': serializer.errors},
                status=HTTP_400_BAD_REQUEST
            )
        
        membership = serializer.save()
        
        logger.info(
            'Channel member added: channel=%s user=%s',
            channel.id,
            membership.user.id
        )
        
        return Response(
            {
                'message': 'Member added successfully',
                'data': ChannelMembershipSerializer(membership).data,
            },
            status=HTTP_201_CREATED
        )
    
    def _remove_member(self, request: Request, channel: Channel) -> Response:
        """Remove member from private channel."""
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required.'},
                status=HTTP_400_BAD_REQUEST
            )
        
        membership = ChannelMembership.objects.filter(
            channel=channel,
            user_id=user_id
        ).first()
        
        if not membership:
            return Response(
                {'error': 'User is not a member of this channel.'},
                status=HTTP_404_NOT_FOUND
            )
        
        membership.delete()
        
        logger.info(
            'Channel member removed: channel=%s user=%s',
            channel.id,
            user_id
        )
        
        return Response(
            {'message': 'Member removed successfully'},
            status=HTTP_204_NO_CONTENT
        )