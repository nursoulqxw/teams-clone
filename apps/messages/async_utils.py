import asyncio
import aiohttp
from apps.messages.models import Message


async def fetch_message_stats_async(channel_id: int) -> dict:
    total, replies, recent = await asyncio.gather(
        Message.objects.filter(channel_id=channel_id).acount(),
        Message.objects.filter(channel_id=channel_id, parent_message__isnull = False).acount(),
        Message.objects.filter(channel_id=channel_id).order_by("-created_at").afirst(),
    )

    return {
        "total_messages": total,
        "total_replies": replies,
        "last_messages": str(recent.content) if recent else None,
    }

BANNED_WORDS = ["spam", "advertisement", "buy now"] #what in the world?

async def process_message_async(content: str) -> dict:
    content = content.strip()

    #spam check
    lower = content.lower()
    is_spam = any(word in lower for word in BANNED_WORDS)

    if is_spam:
        return {"ok": False, "reason": "Message flagged as spam"}
    
    return {"ok": True, "content": content}
        