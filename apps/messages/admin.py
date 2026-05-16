# Django modules
from django.contrib.admin import register, ModelAdmin, TabularInline

# Project modules
from .models import Message


class ReplyInline(TabularInline):
    """Inline admin view for replies nested under a parent message."""

    model = Message
    fk_name = "parent_message"
    extra = 0
    fields = ("author", "content", "created_at")
    readonly_fields = ("author", "created_at")
    show_change_link = True


@register(Message)
class MessageAdmin(ModelAdmin):
    """Admin configuration for the Message model."""

    SHORT_CONTENT_LENGTH = 60

    list_display = (
        "id",
        "author",
        "channel",
        "short_content",
        "has_replies",
        "created_at",
        "updated_at",
    )
    list_filter = ("channel", "author", "created_at")
    search_fields = (
        "content",
        "author__email",
        "author__first_name",
        "author__last_name",
    )
    raw_id_fields = ("author", "channel", "parent_message")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = (ReplyInline,)

    def short_content(self, obj: Message) -> str:
        """Returns a truncated preview of the message content."""
        if len(obj.content) > self.SHORT_CONTENT_LENGTH:
            return obj.content[:self.SHORT_CONTENT_LENGTH] + "..."
        return obj.content

    short_content.short_description = "Content"

    def has_replies(self, obj: Message) -> bool:
        """Returns True if the message has at least one reply."""
        return obj.replies.exists()

    has_replies.boolean = True
    has_replies.short_description = "Has replies"
