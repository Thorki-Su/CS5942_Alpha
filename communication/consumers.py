import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

async def close_chat_room(room_name):
    group_name = f'chat_{room_name}'
    await channel_layer.group_send(
        group_name,
        {
            'type': 'close_room',
        }
    )

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from task.models import Task, TaskApplication
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = self.scope['user']

        self.is_task_group = self.room_name.startswith('task_')
        if self.is_task_group:
            task_id = int(self.room_name.split('_')[1])
            task = await asyncio.to_thread(Task.objects.get, id=task_id)
            if task.status in ['completed', 'cancelled']:
                await self.close()
                return
            if not (task.client == self.user or TaskApplication.objects.filter(task=task, volunteer=self.user, status='accepted').exists()):
                await self.close()
                return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        audio_data = text_data_json.get('audio_data')

        if message:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.scope['user'].email,
                    'is_task_group': self.is_task_group
                }
            )
        if audio_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'audio_message',
                    'audio_data': audio_data,
                    'sender': self.scope['user'].email
                }
            )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        is_task_group = event.get('is_task_group', False)
        receiver = None if is_task_group else self.scope['user'].email
        await self.save_message(sender, receiver, message, is_task_group)
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'is_task_group': is_task_group
        }))

    async def audio_message(self, event):
        audio_data = event['audio_data']
        sender = event['sender']
        await self.send(text_data=json.dumps({
            'audio_data': audio_data,
            'sender': sender
        }))

    async def close_room(self, event):
        await self.close()

    async def save_message(self, sender_email, receiver_email, message, is_task_group):
        from django.contrib.auth import get_user_model
        from task.models import Task, TaskApplication
        from communication.models import ChatMessage
        User = get_user_model()
        sender = await asyncio.to_thread(User.objects.get, email=sender_email)
        task = None
        if is_task_group:
            task_id = int(self.room_name.split('_')[1])
            task = await asyncio.to_thread(Task.objects.get, id=task_id)
        ChatMessage.objects.create(
            sender=sender,
            receiver=None if is_task_group else await asyncio.to_thread(User.objects.get, email=receiver_email),
            content=message,
            task=task
        )

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from task.models import Task, TaskApplication
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'video_{self.room_name}'
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = self.scope['user']

        self.is_task_group = self.room_name.startswith('task_')
        if self.is_task_group:
            task_id = int(self.room_name.split('_')[1])
            task = await asyncio.to_thread(Task.objects.get, id=task_id)
            if task.status in ['completed', 'cancelled']:
                await self.close()
                return
            if not (task.client == self.user or TaskApplication.objects.filter(task=task, volunteer=self.user, status='accepted').exists()):
                await self.close()
                return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        signal = text_data_json.get('signal')
        audio_data = text_data_json.get('audio_data')

        if signal:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_signal',
                    'signal': signal,
                    'sender': self.scope['user'].email
                }
            )
        if audio_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'audio_message',
                    'audio_data': audio_data,
                    'sender': self.scope['user'].email
                }
            )

    async def video_signal(self, event):
        signal = event['signal']
        sender = event['sender']
        await self.send(text_data=json.dumps({
            'signal': signal,
            'sender': sender
        }))

    async def audio_message(self, event):
        audio_data = event['audio_data']
        sender = event['sender']
        await self.send(text_data=json.dumps({
            'audio_data': audio_data,
            'sender': sender
        }))