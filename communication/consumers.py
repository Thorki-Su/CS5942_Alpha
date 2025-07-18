import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from task.models import Task, TaskApplication
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from communication.models import ChatMessage, OneToOneChatSession
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import logging

# 配置日志
logger = logging.getLogger(__name__)

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

@sync_to_async
def get_or_create_one_to_one_room(user1_email, user2_email):
    User = get_user_model()
    try:
        print(f"Attempting to get or create room for {user1_email} and {user2_email} in consumer")  # 调试日志
        user1 = User.objects.get(email=user1_email, is_active=True)  # 添加 is_active 一致性
        print(f"Found user1: {user1.email}, id={user1.id}, is_active={user1.is_active}")  # 调试日志
        user2 = User.objects.get(email=user2_email, is_active=True)  # 添加 is_active 一致性
        print(f"Found user2: {user2.email}, id={user2.id}, is_active={user2.is_active}")  # 调试日志
        user_ids = sorted([user1.id, user2.id])
        room_name = f"1v1_{user_ids[0]}_{user_ids[1]}"
        print(f"Generated room_name: {room_name}")  # 调试日志
        existing_sessions = OneToOneChatSession.objects.filter(user1__id__in=[user1.id, user2.id], user2__id__in=[user1.id, user2.id])
        if existing_sessions.exists():
            print(f"Existing session found: {existing_sessions[0].room_name}")
            return existing_sessions[0].room_name
        session, created = OneToOneChatSession.objects.get_or_create(
            user1=user1,
            user2=user2,
            defaults={'room_name': room_name}
        )
        print(f"Created OneToOneChatSession: room_name={room_name}, created={created}")  # 调试日志
        return session.room_name
    except User.DoesNotExist as e:
        logger.error(f"User not found in consumer: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_or_create_one_to_one_room in consumer: {e}")
        raise

@sync_to_async
def get_chat_history(room_name):
    if room_name.startswith('chat_task_'):
        task_id = int(room_name.split('_')[2])
        return ChatMessage.objects.filter(task_id=task_id).order_by('timestamp')[:10]
    elif room_name.startswith('1v1_'):
        users = room_name.replace('1v1_', '').split('_')
        return ChatMessage.objects.filter(
            sender__email__in=users,
            receiver__email__in=users
        ).order_by('timestamp')[:10]
    return []

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope['user']
            if not self.user or not self.user.is_authenticated:
                print(f"Error in connect: User not authenticated, scope={self.scope}, headers={dict(self.scope.get('headers', []))}")
                await self.close()
                return

            path = self.scope['path']
            if not path.startswith('/ws/chat/'):
                print(f"Error in connect: Invalid path {path}")
                await self.close()
                return
            self.room_name = path.split('/')[3]
            if not self.room_name:
                print("Error in connect: 'room_name' not found in path")
                await self.close()
                return

            self.room_group_name = f'chat_{self.room_name}'
            self.is_task_group = self.room_name.startswith('chat_task_')
            self.is_one_to_one = self.room_name.startswith('1v1_')

            # 权限检查
            if self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = await get_task(task_id)
                if task.status in ['completed', 'cancelled']:
                    await self.close()
                    return
                if not await check_task_permission(task, self.user):
                    await self.close()
                    return
            elif self.is_one_to_one:
                users = self.room_name.replace('1v1_', '').split('_')
                if self.user.email not in users:
                    await self.close()
                    return

            # 发送历史消息
            history = await get_chat_history(self.room_name)
            for msg in history:
                await self.send(text_data=json.dumps({
                    'message': msg.content,
                    'sender': msg.sender.email,
                    'timestamp': msg.timestamp.isoformat(),
                    'is_task_group': self.is_task_group or self.is_one_to_one
                }))

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            print(f"Connected to room {self.room_name} for user {self.user.email}")
            await self.accept()
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
                print(f"Disconnected from room {self.room_name} for user {self.user.email}")
        except Exception as e:
            print(f"Error in disconnect: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')
            audio_data = text_data_json.get('audio_data')
            video_signal = text_data_json.get('video_signal')

            if message:
                # 回显给发送者
                await self.send(text_data=json.dumps({
                    'message': message,
                    'sender': self.scope['user'].email,
                    'timestamp': timezone.now().isoformat(),
                    'is_task_group': self.is_task_group or self.is_one_to_one
                }))
                # 发送给组
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.scope['user'].email,
                    'is_task_group': self.is_task_group or self.is_one_to_one
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
            receiver = None if is_task_group or self.is_one_to_one else self.scope['user'].email
            await self.save_message(sender, receiver, message, is_task_group or self.is_one_to_one)
            # 广播给组中其他成员，排除发送者自己的回显
            if self.channel_name != self.channel_layer._get_channel_name_from_group(self.room_group_name):
                await self.send(text_data=json.dumps({
                    'message': message,
                    'sender': sender,
                    'timestamp': timezone.now().isoformat(),
                    'is_task_group': is_task_group or self.is_one_to_one
                }))
        except Exception as e:
            print(f"Error in chat_message: {e}")

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

    async def save_message(self, sender_email, receiver_email, message, is_task_group_or_one_to_one):
        try:
            from django.contrib.auth import get_user_model
            from task.models import Task
            from communication.models import ChatMessage
            User = get_user_model()
            sender = await asyncio.to_thread(User.objects.get, email=sender_email)
            task = None
            if is_task_group_or_one_to_one and self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = await get_task(task_id)
            ChatMessage.objects.create(
                sender=sender,
                receiver=None if is_task_group_or_one_to_one else await asyncio.to_thread(User.objects.get, email=receiver_email),
                content=message,
                task=task,
                timestamp=timezone.now()
            )
        except Exception as e:
            print(f"Error in save_message: {e}")

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope['user']
            if not self.user or not self.user.is_authenticated:
                print(f"Error in connect: User not authenticated, scope={self.scope}, headers={dict(self.scope.get('headers', []))}")
                await self.close()
                return

            path = self.scope['path']
            if not path.startswith('/ws/video/'):
                print(f"Error in connect: Invalid path {path}")
                await self.close()
                return
            self.room_name = path.split('/')[3]
            if not self.room_name:
                print("Error in connect: 'room_name' not found in path")
                await self.close()
                return

            self.room_group_name = f'video_{self.room_name}'
            self.is_task_group = self.room_name.startswith('chat_task_')
            self.is_one_to_one = self.room_name.startswith('1v1_')

            if self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = await get_task(task_id)
                if task.status in ['completed', 'cancelled']:
                    await self.close()
                    return
                if not await check_task_permission(task, self.user):
                    await self.close()
                    return
            elif self.is_one_to_one:
                users = self.room_name.replace('1v1_', '').split('_')
                if self.user.email not in users:
                    await self.close()
                    return

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            print(f"Connected to video room {self.room_name} for user {self.user.email}")
            await self.accept()
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
                print(f"Disconnected from video room {self.room_name} for user {self.user.email}")
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