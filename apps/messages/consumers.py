import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .async_utils import fetch_message_stats_async, process_message_async


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.channel_id = self.scope["url_route"]["kwargs"]["channel_id"]
        self.room_group_name = f"chat_{self.channel_id}"

        # need to comment this out for now since we don't have auth set up yet, but in a real app you'd want to check if the user is authenticated before allowing them to connect
        user = self.scope["user"]  #<--
        if not user.is_authenticated: #<--
            await self.close() #<--
            return #<--
        #------- 3акомментируйте все что я тут указал, чтобы протестить через терминал (удобнее), но лучше все таки через авторизацию тестить (правильнее)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        # send connection confirmation + channel stats to the joining client
        stats = await fetch_message_stats_async(self.channel_id)
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "You're now connected",
            "stats": stats,
        }))

    async def disconnect(self, _close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        """Called automatically when the client sends a message."""
        data = json.loads(text_data)
        raw_content = data.get("message", "")

        # process (spam check + clean) before broadcasting
        result = await process_message_async(raw_content)
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

    async def chat_message(self, event):
        """Called by the channel layer for every member in the group."""
        await self.send(text_data=json.dumps({
            "type": "chat",
            "message": event["message"],
            "sender": event["sender"],
        }))
