import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from task.models import Task, TaskApplication
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

async def close_chat_room(room_name):
    group_name = f'chat_{room_name}'
    try:
        await channel_layer.group_send(
            group_name,
            {
                'type': 'close_room',
            }
        )
    except Exception as e:
        print(f"Error closing chat room {room_name}: {e}")

@sync_to_async
def get_task(task_id):
    return Task.objects.get(id=task_id)

@sync_to_async
def check_task_permission(task, user):
    from task.models import TaskApplication
    return task.client == user or TaskApplication.objects.filter(task=task, volunteer=user, status='accepted').exists()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.user = self.scope['user']
            if not self.user.is_authenticated:
                await self.close()
                return

            path = self.scope['path']
            if not path.startswith('/ws/chat/'):
                print(f"Error in connect: Invalid path {path}")
                await self.close()
                return
            self.room_name = path.split('/')[3]  # 提取 room_name，例如 chat_task_1
            if not self.room_name:
                print("Error in connect: 'room_name' not found in path")
                await self.close()
                return

            self.room_group_name = f'chat_{self.room_name}'
            self.is_task_group = self.room_name.startswith('chat_task_')
            if self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = await get_task(task_id)
                if task.status in ['completed', 'cancelled']:
                    await self.close()
                    return
                if not await check_task_permission(task, self.user):
                    await self.close()
                    return

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception as e:
            print(f"Error in disconnect: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')
            audio_data = text_data_json.get('audio_data')
            video_signal = text_data_json.get('video_signal')

            if message:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.scope['user'].email,
                    'is_task_group': self.is_task_group
                })
            if audio_data:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'audio_message',
                    'audio_data': audio_data,
                    'sender': self.scope['user'].email
                })
            if video_signal:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'video_signal',
                    'signal': video_signal,
                    'sender': self.scope['user'].email
                })
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    async def chat_message(self, event):
        try:
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
        except Exception as e:
            print(f"Error in chat_message: {e}")

    async def audio_message(self, event):
        try:
            audio_data = event['audio_data']
            sender = event['sender']
            if audio_data == 'toggle':
                await self.send(text_data=json.dumps({
                    'audio_data': 'toggle',
                    'sender': sender
                }))
            else:
                await self.send(text_data=json.dumps({
                    'audio_data': audio_data,
                    'sender': sender
                }))
        except Exception as e:
            print(f"Error in audio_message: {e}")

    async def video_signal(self, event):
        try:
            video_signal = event['signal']
            sender = event['sender']
            await self.send(text_data=json.dumps({
                'video_signal': video_signal,
                'sender': sender
            }))
        except Exception as e:
            print(f"Error in video_signal: {e}")

    async def close_room(self, event):
        try:
            await self.close()
        except Exception as e:
            print(f"Error in close_room: {e}")

    async def save_message(self, sender_email, receiver_email, message, is_task_group):
        try:
            from django.contrib.auth import get_user_model
            from task.models import Task, TaskApplication
            from communication.models import ChatMessage
            User = get_user_model()
            sender = await asyncio.to_thread(User.objects.get, email=sender_email)
            task = None
            if is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = await get_task(task_id)
            ChatMessage.objects.create(
                sender=sender,
                receiver=None if is_task_group else await asyncio.to_thread(User.objects.get, email=receiver_email),
                content=message,
                task=task
            )
        except Exception as e:
            print(f"Error in save_message: {e}")

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.user = self.scope['user']
            if not self.user.is_authenticated:
                await self.close()
                return

            path = self.scope['path']
            if not path.startswith('/ws/video/'):
                print(f"Error in connect: Invalid path {path}")
                await self.close()
                return
            self.room_name = path.split('/')[3]  # 提取 room_name，例如 chat_task_1
            if not self.room_name:
                print("Error in connect: 'room_name' not found in path")
                await self.close()
                return

            self.room_group_name = f'video_{self.room_name}'
            self.is_task_group = self.room_name.startswith('chat_task_')
            if self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = await get_task(task_id)
                if task.status in ['completed', 'cancelled']:
                    await self.close()
                    return
                if not await check_task_permission(task, self.user):
                    await self.close()
                    return

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception as e:
            print(f"Error in disconnect: {e}")

    async def receive(self, text_data):
        try:
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
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    async def video_signal(self, event):
        try:
            signal = event['signal']
            sender = event['sender']
            await self.send(text_data=json.dumps({
                'signal': signal,
                'sender': sender
            }))
        except Exception as e:
            print(f"Error in video_signal: {e}")

    async def audio_message(self, event):
        try:
            audio_data = event['audio_data']
            sender = event['sender']
            await self.send(text_data=json.dumps({
                'audio_data': audio_data,
                'sender': sender
            }))
        except Exception as e:
            print(f"Error in audio_message: {e}")