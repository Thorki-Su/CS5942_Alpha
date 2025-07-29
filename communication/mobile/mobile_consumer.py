# communication/mobile/mobile_video_consumer.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class MobileVideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_name = f'task-{self.task_id}'
        self.room_group_name = f'video_{self.room_name}'

        # 验证任务和用户身份
        valid = await self.validate_user_and_task()
        if not valid:
            await self.close()
            return

        # 加入房间
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # 转发信令数据（WebRTC signaling）
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video.signal',
                'message': text_data,
            }
        )

    async def video_signal(self, event):
        await self.send(text_data=event['message'])

    @database_sync_to_async
    def validate_user_and_task(self):
        from task.models import Task
        from django.contrib.auth import get_user_model
        User = get_user_model()  # ✅ 延迟调用 ORM
        
        try:
            task = Task.objects.get(id=self.task_id)

            if task.status not in ['accepted', 'ongoing']:
                return False

            user = self.scope['user']
            # 校验当前用户是否为参与者
            return task.client == user or task.volunteer == user

        except Task.DoesNotExist:
            return False
