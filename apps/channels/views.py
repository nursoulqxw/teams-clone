# Python modules
import logging
from django.db.models import Q, Count
# Rest modules
from rest_framework import serializers
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
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    inline_serializer,
)

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
from .filters import ChannelFilter
from django.core.cache import cache
from .cache import invalidate_channel_cache, invalidate_team_channels_cache

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
    filter_backends = [DjangoFilterBackend]
    filterset_class = ChannelFilter

    def get_queryset(self):
        """
        A basic QuerySet with query optimization and annotations (N+1 avoidance).
        The user sees all public communication channels and their own private ones.
        """
        user = self.request.user
        qs = Channel.objects.select_related('team').prefetch_related(
            'members', 'channel_messages'
        ).annotate(
            members_count=Count('members', distinct=True),
            messages_count=Count('channel_messages', distinct=True)
        )
        return qs.filter(
            Q(is_private=False) | Q(is_private=True, members=user)
        ).distinct()
    
    def get_channel_or_404(self, pk: int) -> tuple[Channel | None, Response | None]:
        try:
            channel = self.get_queryset().get(pk=pk)
            self.check_object_permissions(self.request, channel)
            return channel, None
        except Channel.DoesNotExist:
            logger.warning('Channel not found: id=%s', pk)
            return None, Response(
                {'error': _('Channel not found.')},
                status=HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Получить список каналов",
        description=(
            "Возвращает список всех публичных каналов команды, "
            "а также приватные каналы, в которых состоит текущий пользователь."
        ),
        parameters=[
            OpenApiParameter(
                name='team_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='ID команды для фильтрации каналов'
            ),
            OpenApiParameter(
                name='team',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Альтернативный параметр ID команды'
            ),
        ],
        responses={200: ChannelSerializer(many=True)}
    )
    def list(self, request: Request) -> Response:
        """
        GET /api/channels/?team_id={id}
        List all channels in a team.
        Required query parameter: team_id
        """
        team_id = request.query_params.get('team') or request.query_params.get('team_id')
        
        if not team_id:
            return Response(
                {'error': _('team_id query parameter is required.')},
                status=HTTP_400_BAD_REQUEST
            )
        
        try:
            team_id = int(team_id)
        except (ValueError, TypeError):
            return Response(
                {'error': _('team_id must be a valid integer.')},
                status=HTTP_400_BAD_REQUEST
            )

        user = request.user
        
        # 1. Формируем ключ кэша, УЧИТЫВАЯ параметры фильтрации (urlencode)
        query_string = request.GET.urlencode()
        cache_key = f"channels_team_{team_id}_user_{user.id}_params_{query_string}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info('Channels listed from CACHE: team=%s user=%s', team_id, user.id)
            return Response(cached_data, status=HTTP_200_OK)
        
        # 2. Получаем базовый QuerySet (где уже есть select_related, prefetch_related и аннотации)
        queryset = self.get_queryset()
        
        # Применяем django-filters
        filterset = self.filterset_class(request.query_params, queryset=queryset, request=request)
        if filterset.is_valid():
            queryset = filterset.qs
        else:
            return Response(filterset.errors, status=HTTP_400_BAD_REQUEST)
            
        # Обязательно ограничиваем выдачу по команде и сортируем
        queryset = queryset.filter(team_id=team_id).order_by('name')
        
        serializer = ChannelSerializer(queryset, many=True)
        response_data = {
            'message': _('List of channels'),
            'count': queryset.count(),
            'data': serializer.data,
        }

        # 3. Сохраняем результат в кэш на 5 минут
        cache.set(cache_key, response_data, timeout=300)
        
        logger.info(
            'Channels listed from DB: team=%s user=%s count=%s',
            team_id,
            user.id,
            queryset.count()
        )
        
        return Response(response_data, status=HTTP_200_OK)
    
    @extend_schema(
        summary="Получить детали канала",
        description="Возвращает подробную информацию о конкретном канале по его ID.",
        responses={200: ChannelSerializer()}
    )
    def retrieve(self, request: Request, pk: int = None) -> Response:
        """
        GET /api/channels/{id}/
        Retrieve one channel.
        """
        # get_channel_or_404 уже использует get_queryset(), 
        # который сам отсечет приватные каналы, к которым нет доступа.
        channel, error = self.get_channel_or_404(pk)
        if error:
            return error

        # 1. Проверяем кэш для сериализованных данных
        cache_key = f"channel_{pk}"
        cached_channel_data = cache.get(cache_key)

        if cached_channel_data:
            logger.info('Channel retrieved from CACHE: id=%s by user=%s', pk, request.user.id)
            return Response(
                {
                    'message': _('Channel detail'),
                    'data': cached_channel_data,
                },
                status=HTTP_200_OK
            )
        
        # 2. Если в кэше нет — сериализуем и сохраняем
        serializer = ChannelSerializer(channel)
        cache.set(cache_key, serializer.data, timeout=600)  # 10 минут
        
        logger.info(
            'Channel retrieved from DB: id=%s by user=%s',
            pk,
            request.user.id
        )
        
        return Response(
            {
                'message': _('Channel detail'),
                'data': serializer.data,
            },
            status=HTTP_200_OK
        )
    
    @extend_schema(
        summary="Создать канал",
        description="Создает новый канал в указанной команде.",
        request=CreateChannelSerializer,
        responses={201: ChannelSerializer()}
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

        # ИНВАЛИДАЦИЯ: Сбрасываем кэш списков каналов для всей команды
        invalidate_team_channels_cache(channel.team.id)
        
        logger.info(
            'Channel created: id=%s name=%s team=%s by user=%s',
            channel.id,
            channel.name,
            channel.team.id,
            request.user.id
        )
        
        return Response(
            {
                'message': _('Channel created successfully'),
                'data': ChannelSerializer(channel).data,
            },
            status=HTTP_201_CREATED
        )
    
    @extend_schema(
        summary="Обновить канал",
        description="Частично обновляет данные существующего канала.",
        request=UpdateChannelSerializer,
        responses={200: ChannelSerializer()}
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

        # ИНВАЛИДАЦИЯ: Сбрасываем кэш самого канала и списков команды
        invalidate_channel_cache(channel.id)
        invalidate_team_channels_cache(channel.team.id)
        
        logger.info(
            'Channel updated: id=%s by user=%s',
            channel.id,
            request.user.id
        )
        
        return Response(
            {
                'message': _('Channel updated successfully'),
                'data': ChannelSerializer(channel).data,
            },
            status=HTTP_200_OK
        )
    
    @extend_schema(
        summary="Удалить канал",
        description="Полностью удаляет канал по его ID.",
        responses={204: None}
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
        team_id = channel.team.id
        
        channel.delete()

        # ИНВАЛИДАЦИЯ: Сбрасываем кэш удаленного канала и списков команды
        invalidate_channel_cache(channel_id)
        invalidate_team_channels_cache(team_id)
        
        logger.info(
            'Channel deleted: id=%s name=%s by user=%s',
            channel_id,
            channel_name,
            request.user.id
        )
        
        return Response(
            {'message': _('Channel deleted successfully')},
            status=HTTP_204_NO_CONTENT
        )
    
    @extend_schema(
        methods=['GET'],
        summary="Список участников канала",
        description="Возвращает список всех участников приватного канала.",
        responses={200: ChannelMembershipSerializer(many=True)}
    )
    @extend_schema(
        methods=['POST'],
        summary="Добавить участника в канал",
        description="Добавляет нового пользователя в приватный канал.",
        request=AddChannelMemberSerializer,
        responses={201: ChannelMembershipSerializer()}
    )
    @extend_schema(
        methods=['DELETE'],
        summary="Удалить участника из канала",
        description="Удаляет пользователя из приватного канала по его user_id.",
        request=inline_serializer(
            name='RemoveMemberSerializer',
            fields={'user_id': serializers.IntegerField(help_text="ID пользователя для удаления")}
        ),
        responses={204: None}
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
                {'error': _('This endpoint is only for private channels.')},
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
                'message': _('List of channel members'),
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

        # Если состав участников канала изменился, его количество участников тоже,
        # так что на всякий случай инвалидируем кэш деталей канала и списков.
        invalidate_channel_cache(channel.id)
        invalidate_team_channels_cache(channel.team.id)
        
        logger.info(
            'Channel member added: channel=%s user=%s',
            channel.id,
            membership.user.id
        )
        
        return Response(
            {
                'message': _('Member added successfully'),
                'data': ChannelMembershipSerializer(membership).data,
            },
            status=HTTP_201_CREATED
        )
    
    def _remove_member(self, request: Request, channel: Channel) -> Response:
        """Remove member from private channel."""
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': _('user_id is required.')},
                status=HTTP_400_BAD_REQUEST
            )
        
        membership = ChannelMembership.objects.filter(
            channel=channel,
            user_id=user_id
        ).first()
        
        if not membership:
            return Response(
                {'error': _('User is not a member of this channel.')},
                status=HTTP_404_NOT_FOUND
            )
        
        membership.delete()

        # Также инвалидируем кэш при удалении участника
        invalidate_channel_cache(channel.id)
        invalidate_team_channels_cache(channel.team.id)
        
        logger.info(
            'Channel member removed: channel=%s user=%s',
            channel.id,
            user_id
        )
        
        return Response(
            {'message': _('Member removed successfully')},
            status=HTTP_204_NO_CONTENT
        )