# Python imports
import logging

# DRF imports
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
    CharField,
    PrimaryKeyRelatedField,
)

# Project imports
from .models import Message
from apps.users.serializers import UserListSerializer
from apps.channels.models import Channel
from apps.channels.serializers import ChannelSerializer

logger = logging.getLogger(__name__)


class MessageSerializer(ModelSerializer):
    """
    Read-only serializer for Message.
    Used in: list, retrieve
    """

    author = UserListSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)

    replies_count = SerializerMethodField()

    class Meta:
        model = Message
        fields = "__all__"

    def get_replies_count(self, obj):
        return obj.replies.count()


class CreateMessageSerializer(ModelSerializer):
    """
    Serializer for creating a Message.
    Used in: create
    """

    content = CharField(min_length=1, trim_whitespace=True)

    channel = PrimaryKeyRelatedField(queryset=Channel.objects.all())

    parent_message = PrimaryKeyRelatedField(
        queryset=Message.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Message
        fields = ["content", "channel", "parent_message"]

    def validate(self, attrs):
        """
        Validate message data:
        - user must be authenticated
        - user must be a member of the channel's team
        - parent_message (if set) must belong to the same channel
        """

        request = self.context.get("request")
        user = request.user if request else None

        channel = attrs["channel"]
        parent_message = attrs.get("parent_message")

        # 1) Auth check
        if not user or not user.is_authenticated:
            raise ValidationError("Authentication error")

        # 2) Permission check (user must be in team)
        if not channel.team.members.filter(id=user.id).exists():
            logger.warning(
                "Message create denied (not team member): user=%s channel=%s team=%s",
                user.id,
                channel.id,
                channel.team_id,
            )
            raise ValidationError("You have no access to this channel.")

        # 3) Thread check (parent must be in same channel)
        if parent_message and parent_message.channel_id != channel.id:
            logger.warning(
                "Message create denied (parent channel mismatch): user=%s channel=%s parent=%s parent_channel=%s",
                user.id,
                channel.id,
                parent_message.id,
                parent_message.channel_id,
            )
            raise ValidationError(
                {"parent_message": "Parent message must be in the same channel."}
            )

        return attrs
    
    def create(self, validation_data: dict) -> Message:
        request = self.context.get("request")

        message = Message.objects.create(
            author = request.user,
            **validation_data
        )

        logger.info(
            "message created: id=%s channel=%s author=%s parent=%s",
            message.id, message.channel_id, message.author_id, message.parent_message_id
        )

        return message
    
class UpdateMessageSerializer(ModelSerializer):
    """
    UPDATE serializer (PATCH/PUT)
    
    """

    content = CharField(min_length = 1, trim_whitespace = True, required = True)

    class Meta:
        model = Message
        fields = ["content"]

    def validate(self, attrs: dict) -> dict:
        request = self.context.get("request")
        user = request.user if request else None

        if not user or not user.is_authenticated:
            raise ValidationError("Authentication required.")

        # 
        if self.instance.author_id != user.id:
            logger.warning(
                "Message update denied (not author): msg=%s user=%s author=%s",
                self.instance.id, user.id, self.instance.author_id
            )
            raise ValidationError("Only the author can edit this message.")

        return attrs

    def update(self, instance: Message, validated_data: dict) -> Message:
        instance.content = validated_data.get("content", instance.content)
        instance.save(update_fields=["content", "updated_at"])

        logger.info(
            "Message updated: id=%s author=%s",
            instance.id, instance.author_id
        )

        return instance