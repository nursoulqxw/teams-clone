from django.contrib.admin import register, ModelAdmin

from .models import Message


@register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ("id", "author", "channel", "short_content", "created_at", "updated_at")
    list_filter = ("channel", "author", "created_at")
    search_fields = ("content", "author__email", "author__first_name", "author__last_name")
    raw_id_fields = ("author", "channel", "parent_message")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def short_content(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
    short_content.short_description = "Content"
