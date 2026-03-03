#Python modules
import logging

#Rest modules
from django.shortcuts import render
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
from rest_framework.permissions import IsAuthenticated

from .models import Message
from .serializers import (
    MessageSerializer,
    CreateMessageSerializer,
    UpdateMessageSerializer,
)

logger = logging.getLogger(__name__)

class MessageViewSet(ViewSet):
    """
    Message endpoints:
        GET    api/messages/           - list messages (optionally ?channel=<id>)
        POST   api/messages/           - create message
        GET    api/messages/{id}/      - retrieve message
        PATCH  api/messages/{id}/      - update message
        DELETE api/messages/{id}/      - delete message
    """

    permission_classes = [IsAuthenticated]

    def get_message_or_404(
        self,
        pk: int
    ) -> tuple[Message | None, Response | None]:
        """Helper: returns (message, None) or (None, 404 Response)"""
        try:
            message = Message.objects.select_related(
                "author",
                "channel",
                "channel__team",
            ).get(pk=pk)
            return message, None
        except Message.DoesNotExist:
            logger.warning("Message not found: id=%s", pk)
            return None, Response(
                {"error": "Message not found"},
                status=HTTP_404_NOT_FOUND
            )
        
    def _user_has_channel_access(
        self,
        user,
        channel
    ) -> bool:
        """
        True если user состоит в team канала.
        Ожидается: channel.team.members (ManyToMany на users)
        """
        try:
            return channel.team.members.filter(id=user.id).exists()
        except Exception:
            return False
        


    def list(self, request: Request) -> Response:
        """
        GET api/messages/ — list messages
        Optional filter: ?channel=<id>
        """
        user = request.user
        channel_id = request.query_params.get("channel")

        queryset = Message.objects.select_related(
            "author",
            "channel",
            "channel__team",
        ).prefetch_related(
            "replies"
        ).filter(
            channel__team__members__id=user.id
        ).order_by("created_at")

        if channel_id:
            queryset = queryset.filter(channel_id = channel_id)

        serializer = MessageSerializer(queryset, many = True)
        logger.debug("Message list requested by user=%s channel=%s", user.id, channel_id)

        return Response(
            {
                "message": "List of messages",
                "count": queryset.count(),
                "data": serializer.data,
            },
            status=HTTP_200_OK,
        )
    
    def retrieve(self, request: Request, pk: int = None) -> Response:
        """GET api/messages/{id}/ — retrieve one message"""
        user = request.user
        message, error = self.get_message_or_404(pk)
        if error:
            return error

        # access check
        if not self._user_has_channel_access(user, message.channel):
            logger.warning(
                "Message retrieve denied (not team member): user=%s msg=%s channel=%s team=%s",
                user.id, message.id, message.channel_id, message.channel.team_id
            )
            return Response(
                {"error": "You have no access to this channel."},
                status=HTTP_404_NOT_FOUND,  # часто отдают 404 чтобы не палить существование
            )

        serializer = MessageSerializer(message)
        logger.info("Message retrieved: id=%s by user=%s", message.id, user.id)

        return Response(
            {
                "message": "Message detail",
                "data": serializer.data,
            },
            status=HTTP_200_OK,
        )

    def create(self, request: Request) -> Response:
        """POST api/messages/ — create a message"""
        serializer = CreateMessageSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            logger.warning(
                "Message creation failed: user=%s errors=%s",
                request.user.id,
                serializer.errors,
            )
            return Response(
                {"error": serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )

        message = serializer.save()

        return Response(
            {
                "message": "Message created successfully",
                "data": MessageSerializer(message).data,
            },
            status=HTTP_201_CREATED,
        )

    def partial_update(self, request: Request, pk: int = None) -> Response:
        """PATCH api/messages/{id}/ — update message (content only)"""
        user = request.user
        message, error = self.get_message_or_404(pk)
        if error:
            return error

        # доступ к каналу (на всякий)
        if not self._user_has_channel_access(user, message.channel):
            logger.warning(
                "Message update denied (not team member): user=%s msg=%s channel=%s",
                user.id, message.id, message.channel_id
            )
            return Response(
                {"error": "You have no access to this channel."},
                status=HTTP_404_NOT_FOUND,
            )

        serializer = UpdateMessageSerializer(
            message,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        if not serializer.is_valid():
            logger.warning(
                "Message update failed: msg=%s errors=%s",
                message.id,
                serializer.errors,
            )
            return Response(
                {"error": serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )

        message = serializer.save()

        return Response(
            {
                "message": "Message updated successfully",
                "data": MessageSerializer(message).data,
            },
            status=HTTP_200_OK,
        )

    def destroy(self, request: Request, pk: int = None) -> Response:
        """DELETE api/messages/{id}/ — delete message"""
        user = request.user
        message, error = self.get_message_or_404(pk)
        if error:
            return error

        # доступ к каналу
        if not self._user_has_channel_access(user, message.channel):
            logger.warning(
                "Message delete denied (not team member): user=%s msg=%s channel=%s",
                user.id, message.id, message.channel_id
            )
            return Response(
                {"error": "You have no access to this channel."},
                status=HTTP_404_NOT_FOUND,
            )

        # правило: удалять может только автор
        if message.author_id != user.id:
            logger.warning(
                "Message delete denied (not author): msg=%s user=%s author=%s",
                message.id, user.id, message.author_id
            )
            return Response(
                {"error": "Only the author can delete this message."},
                status=HTTP_400_BAD_REQUEST,
            )

        msg_id = message.id
        message.delete()

        logger.info("Message deleted: id=%s by user=%s", msg_id, user.id)

        return Response(
            {"message": "Message deleted successfully"},
            status=HTTP_204_NO_CONTENT,
        )
