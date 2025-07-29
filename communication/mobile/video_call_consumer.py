# communication/mobile/video_call_consumer.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope["url_route"]["kwargs"]["task_id"]
        self.room_group_name = f"video_task_{self.task_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"[WebSocket Connected] task-{self.task_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"[WebSocket Disconnected] task-{self.task_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            print(f"[Message Received] {data}")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "video_message",
                    "message": data,
                }
            )
        except Exception as e:
            print(f"[Receive Error] {e}")

    async def video_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
