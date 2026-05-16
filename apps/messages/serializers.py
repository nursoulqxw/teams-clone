# Python modules
import logging
from typing import Any, Optional

# Django modules
from django.utils.translation import gettext_lazy as _

# Django REST Framework
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
    CharField,
    PrimaryKeyRelatedField,
)

# Project modules
from .models import Message
from apps.users.serializers import UserListSerializer
from apps.channels.models import Channel
from apps.channels.serializers import ChannelSerializer

logger = logging.getLogger(__name__)


class MessageSerializer(ModelSerializer):
    """
    Read-only serializer for Message.
    Used in: list, retrieve.
    """

    author = UserListSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    replies_count = SerializerMethodField()

    class Meta:
        """Customization of the Serializer metadata."""

        model = Message
        fields = (
            "id",
            "content",
            "author",
            "channel",
            "parent_message",
            "replies_count",
            "created_at",
            "updated_at",
        )

    def get_replies_count(self, obj: Message) -> int:
        """Returns the number of replies to this message."""
        return obj.replies.count()


class CreateMessageSerializer(ModelSerializer):
    """
    Serializer for creating a Message.
    Used in: create.
    """

    content = CharField(
        min_length=Message.CONTENT_MIN_LENGTH,
        trim_whitespace=True,
    )
    channel = PrimaryKeyRelatedField(
        queryset=Channel.objects.all(),
    )
    parent_message = PrimaryKeyRelatedField(
        queryset=Message.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        """Customization of the Serializer metadata."""

        model = Message
        fields = (
            "content",
            "channel",
            "parent_message",
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        Validate message data:
        - user must be authenticated
        - user must be a member of the channel's team
        - parent_message (if set) must belong to the same channel
        """
        request = self.context.get("request")
        user: Optional[Any] = request.user if request else None

        channel: Channel = attrs["channel"]
        parent_message: Optional[Message] = attrs.get("parent_message")

        if not user or not user.is_authenticated:
            raise ValidationError(_("Authentication error."))

        if not channel.team.members.filter(id=user.id).exists():
            logger.warning(
                "Message create denied (not team member): user=%s channel=%s team=%s",
                user.id,
                channel.id,
                channel.team_id,
            )
            raise ValidationError(_("You have no access to this channel."))

        if parent_message and parent_message.channel_id != channel.id:
            logger.warning(
                "Message create denied (parent channel mismatch): "
                "user=%s channel=%s parent=%s parent_channel=%s",
                user.id,
                channel.id,
                parent_message.id,
                parent_message.channel_id,
            )
            raise ValidationError(
                {"parent_message": _("Parent message must be in the same channel.")}
            )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> Message:
        """Creates and returns a new Message instance."""
        request = self.context.get("request")

        message: Message = Message.objects.create(
            author=request.user,
            **validated_data,
        )

        logger.info(
            "Message created: id=%s channel=%s author=%s parent=%s",
            message.id,
            message.channel_id,
            message.author_id,
            message.parent_message_id,
        )

        return message


class UpdateMessageSerializer(ModelSerializer):
    """
    Serializer for updating a Message (PATCH/PUT).
    Used in: partial_update.
    """

    content = CharField(
        min_length=Message.CONTENT_MIN_LENGTH,
        trim_whitespace=True,
        required=True,
    )

    class Meta:
        """Customization of the Serializer metadata."""

        model = Message
        fields = ("content",)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validates that the requesting user is the message author."""
        request = self.context.get("request")
        user: Optional[Any] = request.user if request else None

        if not user or not user.is_authenticated:
            raise ValidationError(_("Authentication required."))

        if self.instance.author_id != user.id:
            logger.warning(
                "Message update denied (not author): msg=%s user=%s author=%s",
                self.instance.id,
                user.id,
                self.instance.author_id,
            )
            raise ValidationError(_("Only the author can edit this message."))

        return attrs

    def update(self, instance: Message, validated_data: dict[str, Any]) -> Message:
        """Updates and returns the Message instance."""
        instance.content = validated_data.get("content", instance.content)
        instance.save(update_fields=("content", "updated_at"))

        logger.info(
            "Message updated: id=%s author=%s",
            instance.id,
            instance.author_id,
        )

        return instance
