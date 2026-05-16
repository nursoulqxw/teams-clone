# Python modules
import asyncio

# Project modules
from apps.messages.models import Message

BANNED_WORDS: tuple[str, ...] = ("spam", "advertisement", "buy now")


async def fetch_message_stats_async(channel_id: int) -> dict:
    """Returns total message count, reply count, and last message for a channel."""
    total, replies, recent = await asyncio.gather(
        Message.objects.filter(channel_id=channel_id).acount(),
        Message.objects.filter(
            channel_id=channel_id,
            parent_message__isnull=False,
        ).acount(),
        Message.objects.filter(channel_id=channel_id).order_by("-created_at").afirst(),
    )

    return {
        "total_messages": total,
        "total_replies": replies,
        "last_message": str(recent.content) if recent else None,
    }


async def process_message_async(content: str) -> dict:
    """Strips and validates content; rejects messages containing banned words."""
    content = content.strip()
    lower: str = content.lower()

    if any(word in lower for word in BANNED_WORDS):
        return {"ok": False, "reason": "Message flagged as spam."}

    return {"ok": True, "content": content}
