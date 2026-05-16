# Django modules
from django.db.models import (
    Model,
    TextField,
    ForeignKey,
    CASCADE,
    Index,
    DateTimeField,
)
from django.utils.translation import gettext_lazy as _

# Project modules
from apps.users.models import CustomUser
from apps.channels.models import Channel


class Message(Model):
    """Model representing a chat message within a channel."""

    CONTENT_MIN_LENGTH = 1

    content = TextField(
        verbose_name=_("content"),
    )
    author = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE,
        related_name="author_messages",
        verbose_name=_("author"),
    )
    channel = ForeignKey(
        to=Channel,
        on_delete=CASCADE,
        related_name="channel_messages",
        verbose_name=_("channel"),
    )
    parent_message = ForeignKey(
        to="self",
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("parent message"),
    )
    created_at = DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at"),
    )
    updated_at = DateTimeField(
        auto_now=True,
        verbose_name=_("updated at"),
    )

    class Meta:
        """Meta options for Message model."""

        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ("created_at",)
        indexes = (
            Index(fields=("channel", "-created_at")),
            Index(fields=("author",)),
            Index(fields=("parent_message",)),
        )
