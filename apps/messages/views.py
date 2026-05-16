# Python modules
import logging
from typing import Any, Optional

# Django modules
from django.utils.translation import gettext_lazy as _

# Django REST Framework
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_204_NO_CONTENT,
)

# drf-spectacular modules
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from drf_spectacular.types import OpenApiTypes

# Project modules
from .models import Message
from .serializers import (
    MessageSerializer,
    CreateMessageSerializer,
    UpdateMessageSerializer,
    MessageListResponseSerializer,
    MessageDetailResponseSerializer,
    MessageErrorSerializer,
    MessageDeletedResponseSerializer,
)
from .filters import build_message_q
from .tasks import send_message_notification
from .permissions import IsAuthorOrReadOnly
from apps.utils.mixins import TeamAccessMixin, LoggingMixin

logger = logging.getLogger(__name__)

MESSAGES_TAG = "Messages"


class MessageViewSet(ViewSet, TeamAccessMixin, LoggingMixin):
    """
    Message endpoints:
        GET    api/messages/       — list messages (optionally ?channel=<id>)
        POST   api/messages/       — create message
        GET    api/messages/{id}/  — retrieve message
        PATCH  api/messages/{id}/  — update message
        DELETE api/messages/{id}/  — delete message
    """

    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)

    def _get_message_or_404(
        self,
        pk: int,
    ) -> tuple[Optional[Message], Optional[Response]]:
        """Returns (message, None) or (None, 404 Response)."""
        try:
            message: Message = Message.objects.select_related(
                "author",
                "channel",
                "channel__team",
            ).get(pk=pk)
            return message, None
        except Message.DoesNotExist:
            logger.warning("Message not found: id=%s", pk)
            return None, Response(
                {"error": _("Message not found.")},
                status=HTTP_404_NOT_FOUND,
            )

    def _user_has_channel_access(self, user: Any, channel: Any) -> bool:
        """Returns True if the user is a member of the channel's team."""
        try:
            return channel.team.members.filter(id=user.id).exists()
        except Exception:
            return False

    @extend_schema(
        summary="List messages",
        description=(
            "Returns all messages from channels the authenticated user belongs to. "
            "Supports optional filtering by channel, author, and full-text search on content."
        ),
        tags=[MESSAGES_TAG],
        parameters=[
            OpenApiParameter(
                name="channel_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter messages by channel ID.",
            ),
            OpenApiParameter(
                name="author_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter messages by author ID.",
            ),
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Full-text search on message content (case-insensitive).",
            ),
        ],
        responses={
            HTTP_200_OK: OpenApiResponse(
                response=MessageSerializer(many=True),
                description="Messages retrieved successfully.",
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
    )
    def list(self, request: Request) -> Response:
        """GET api/messages/ — list messages."""
        user = request.user

        queryset = (
            Message.objects.select_related(
                "author",
                "channel",
                "channel__team",
            )
            .prefetch_related("replies")
            .filter(channel__team__members__id=user.id)
            .order_by("created_at")
        )

        queryset = build_message_q(request, queryset)
        serializer = MessageSerializer(queryset, many=True)

        logger.debug(
            "Message list requested by user=%s params=%s",
            user.id,
            request.query_params.dict(),
        )

        return Response(
            {
                "message": _("List of messages."),
                "count": len(serializer.data),
                "data": serializer.data,
            },
            status=HTTP_200_OK,
        )

    @extend_schema(
        summary="Retrieve a message",
        description=(
            "Returns the full details of a single message by its ID. "
            "The user must be a member of the channel's team. "
            "Returns 404 if the message does not exist or the user has no access."
        ),
        tags=[MESSAGES_TAG],
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Unique ID of the message.",
            ),
        ],
        responses={
            HTTP_200_OK: OpenApiResponse(
                response=MessageSerializer,
                description="Message retrieved successfully.",
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
            HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Message not found or user has no access to this channel.",
            ),
        },
    )
    def retrieve(self, request: Request, pk: int = None) -> Response:
        """GET api/messages/{id}/ — retrieve one message."""
        user = request.user
        message, error = self._get_message_or_404(pk)
        if error:
            return error

        if not self._user_has_channel_access(user, message.channel):
            logger.warning(
                "Message retrieve denied (not team member): "
                "user=%s msg=%s channel=%s team=%s",
                user.id,
                message.id,
                message.channel_id,
                message.channel.team_id,
            )
            return Response(
                {"error": _("You have no access to this channel.")},
                status=HTTP_404_NOT_FOUND,
            )

        serializer = MessageSerializer(message)
        logger.info("Message retrieved: id=%s by user=%s", message.id, user.id)

        return Response(
            {
                "message": _("Message detail."),
                "data": serializer.data,
            },
            status=HTTP_200_OK,
        )

    @extend_schema(
        summary="Create a message",
        description=(
            "Creates a new message in the specified channel. "
            "The user must be a member of the channel's team. "
            "Optionally, a `parent_message` ID can be provided to reply inside a thread — "
            "the parent must belong to the same channel. "
            "An email notification is sent asynchronously after creation."
        ),
        tags=[MESSAGES_TAG],
        request=CreateMessageSerializer,
        responses={
            HTTP_201_CREATED: OpenApiResponse(
                response=MessageSerializer,
                description="Message created successfully.",
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description=(
                    "Validation error: content is empty, user is not a team member, "
                    "or parent message belongs to a different channel."
                ),
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
        examples=[
            OpenApiExample(
                "Simple message",
                value={"content": "Hello team!", "channel": 1},
                request_only=True,
            ),
            OpenApiExample(
                "Thread reply",
                value={"content": "Good point!", "channel": 1, "parent_message": 5},
                request_only=True,
            ),
        ],
    )
    def create(self, request: Request) -> Response:
        """POST api/messages/ — create a message."""
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

        message: Message = serializer.save()
        send_message_notification.delay(message.id, request.user.email)

        return Response(
            {
                "message": _("Message created successfully."),
                "data": MessageSerializer(message).data,
            },
            status=HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a message",
        description=(
            "Partially updates the content of an existing message. "
            "Only the message author can perform this action — other users receive 403. "
            "The user must also be a member of the channel's team. "
            "Only the `content` field can be updated."
        ),
        tags=[MESSAGES_TAG],
        request=UpdateMessageSerializer,
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Unique ID of the message to update.",
            ),
        ],
        responses={
            HTTP_200_OK: OpenApiResponse(
                response=MessageSerializer,
                description="Message updated successfully.",
            ),
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation error: content is empty or missing.",
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                description="You are not the author of this message.",
            ),
            HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Message not found or user has no access to this channel.",
            ),
        },
        examples=[
            OpenApiExample(
                "Update request",
                value={"content": "Updated message text."},
                request_only=True,
            ),
        ],
    )
    def partial_update(self, request: Request, pk: int = None) -> Response:
        """PATCH api/messages/{id}/ — update message content only."""
        user = request.user
        message, error = self._get_message_or_404(pk)
        if error:
            return error

        self.check_object_permissions(request, message)

        if not self._user_has_channel_access(user, message.channel):
            logger.warning(
                "Message update denied (not team member): user=%s msg=%s channel=%s",
                user.id,
                message.id,
                message.channel_id,
            )
            return Response(
                {"error": _("You have no access to this channel.")},
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
                "message": _("Message updated successfully."),
                "data": MessageSerializer(message).data,
            },
            status=HTTP_200_OK,
        )

    @extend_schema(
        summary="Delete a message",
        description=(
            "Permanently deletes a message by its ID. "
            "Only the message author can delete it — other users receive 403. "
            "The user must also be a member of the channel's team. "
            "Returns 204 No Content on success."
        ),
        tags=[MESSAGES_TAG],
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="Unique ID of the message to delete.",
            ),
        ],
        responses={
            HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Message deleted successfully.",
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                description="You are not the author of this message.",
            ),
            HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Message not found or user has no access to this channel.",
            ),
        },
    )
    def destroy(self, request: Request, pk: int = None) -> Response:
        """DELETE api/messages/{id}/ — delete message."""
        user = request.user
        message, error = self._get_message_or_404(pk)
        if error:
            return error

        self.check_object_permissions(request, message)

        if not self._user_has_channel_access(user, message.channel):
            logger.warning(
                "Message delete denied (not team member): user=%s msg=%s channel=%s",
                user.id,
                message.id,
                message.channel_id,
            )
            return Response(
                {"error": _("You have no access to this channel.")},
                status=HTTP_404_NOT_FOUND,
            )

        msg_id: int = message.id
        message.delete()

        logger.info("Message deleted: id=%s by user=%s", msg_id, user.id)

        return Response(
            {"message": _("Message deleted successfully.")},
            status=HTTP_204_NO_CONTENT,
        )
