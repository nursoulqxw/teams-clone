# Python modules
import json

# Channels modules
from channels.generic.websocket import AsyncWebsocketConsumer

# Project modules
from .async_utils import fetch_message_stats_async, process_message_async


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat within a channel."""

    async def connect(self) -> None:
        """Authenticates the user and joins the channel group on connect."""
        self.channel_id: str = self.scope["url_route"]["kwargs"]["channel_id"]
        self.room_group_name: str = f"chat_{self.channel_id}"

        # user = self.scope["user"]
        # if not user.is_authenticated:
        #     await self.close()
        #     return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

        stats: dict = await fetch_message_stats_async(self.channel_id)
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "You're now connected.",
            "stats": stats,
        }))

    async def disconnect(self, _close_code: int) -> None:
        """Removes the client from the channel group on disconnect."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data: str) -> None:
        """Validates and broadcasts an incoming message to the channel group."""
        data: dict = json.loads(text_data)
        raw_content: str = data.get("message", "")

        result: dict = await process_message_async(raw_content)
        if not result["ok"]:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": result["reason"],
            }))
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": result["content"],
                "sender": getattr(self.scope["user"], "email", "anonymous"),
            },
        )

    async def chat_message(self, event: dict) -> None:
        """Forwards a group message to the individual WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": "chat",
            "message": event["message"],
            "sender": event["sender"],
        }))
