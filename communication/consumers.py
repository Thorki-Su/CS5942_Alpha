import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from task.models import Task, TaskApplication
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.exceptions import ChannelFull
from communication.models import ChatMessage, OneToOneChatSession
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user_email = None
            path = self.scope['path']
            if not path.startswith('/ws/chat/'):
                await self.close()
                return
            self.room_name = path.split('/')[3]
            if not self.room_name:
                await self.close()
                return

            self.room_group_name = f'chat_{self.room_name}'
            self.is_task_group = self.room_name.startswith('chat_task_')
            self.is_one_to_one = self.room_name.startswith('1v1_')

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            logger.debug(f"Connected to room {self.room_name} (awaiting authentication)")
            await self.accept()

        except Exception as e:
            logger.error(f"Error in connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
                if self.user_email:
                    logger.debug(f"Disconnected from room {self.room_name} for user {self.user_email} with code {close_code}")
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            logger.debug(f"Received raw data: {text_data}")
            if not self.user_email and text_data_json.get('type') == 'auth':
                self.user_email = text_data_json.get('user_email')
                if not self.user_email:
                    logger.warning("No user authentication provided")
                    await self.close()
                    return
                authenticated = await self.authenticate_user()
                logger.debug(f"Authentication result for {self.user_email}: {authenticated}")
                if not authenticated:
                    logger.error(f"Authentication failed for user {self.user_email} in room {self.room_name}")
                    await self.close()
                    return
                await self.send(json.dumps({'type': 'auth_ack', 'status': 'authenticated', 'user': self.user_email}))
                logger.debug(f"Authenticated user {self.user_email} in room {self.room_name}")
                return  # 严格退出，避免处理其他消息

            if not self.user_email:
                logger.warning("User not authenticated, closing connection")
                await self.close()
                return

            message = text_data_json.get('message')
            audio_data = text_data_json.get('audio_data')
            signal = text_data_json.get('signal')
            candidate = text_data_json.get('candidate')

            if message:
                receiver = await self.get_receiver()
                data = {
                    'message': message,
                    'sender': self.user_email,
                    'receiver': receiver,
                    'timestamp': timezone.now().isoformat(),
                    'is_group': self.is_task_group
                }
                try:
                    await self.send(text_data=json.dumps(data))
                    await self.channel_layer.group_send(self.room_group_name, {
                        'type': 'chat_message',
                        'message': message,
                        'sender': self.user_email,
                        'receiver': receiver,
                        'is_group': self.is_task_group
                    })
                except ChannelFull:
                    logger.error(f"Channel full for room {self.room_name}")
            elif audio_data:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'audio_message',
                    'audio_data': audio_data,
                    'sender': self.user_email
                })
            elif signal:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'video_signal',
                    'signal': signal,
                    'sender': self.user_email,
                    'to': text_data_json.get('to')
                })
            elif candidate:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'candidate',
                    'candidate': candidate,
                    'sender': self.user_email,
                    'to': text_data_json.get('to')
                })
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in receive for room {self.room_name}: {e}")
            await self.close()

    async def auth_ack(self, event):
        logger.debug(f"Received auth_ack for room {self.room_name}")

    @database_sync_to_async
    def authenticate_user(self):
        try:
            if self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = Task.objects.get(id=task_id)
                if task.status in ['completed', 'cancelled']:
                    return False
                User = get_user_model()
                user = User.objects.get(email=self.user_email)
                return task.client == user or TaskApplication.objects.filter(task=task, volunteer=user, status='accepted').exists()
            elif self.is_one_to_one:
                try:
                    session = OneToOneChatSession.objects.get(room_name=self.room_name)
                    valid_emails = [session.user1.email, session.user2.email]
                    return self.user_email in valid_emails
                except OneToOneChatSession.DoesNotExist:
                    logger.error(f"OneToOneChatSession {self.room_name} not found")
                    return False
            return False
        except Exception as e:
            logger.error(f"Authentication error in room {self.room_name}: {e}")
            return False

    @database_sync_to_async
    def get_receiver(self):
        if self.is_one_to_one:
            try:
                session = OneToOneChatSession.objects.get(room_name=self.room_name)
                if self.user_email == session.user1.email:
                    return session.user2.email
                elif self.user_email == session.user2.email:
                    return session.user1.email
            except OneToOneChatSession.DoesNotExist:
                return None
        return None

    async def chat_message(self, event):
        try:
            message = event['message']
            sender = event['sender']
            receiver = event.get('receiver')
            is_group = event.get('is_group', False)
            await self.save_message(sender, receiver, message, is_group)
            await self.send(text_data=json.dumps({
                'message': message,
                'sender': sender,
                'receiver': receiver,
                'timestamp': timezone.now().isoformat(),
                'is_group': is_group
            }))
        except Exception as e:
            logger.error(f"Error in chat_message: {e}")

    async def audio_message(self, event):
        try:
            audio_data = event['audio_data']
            sender = event['sender']
            await self.send(text_data=json.dumps({
                'audio_data': audio_data,
                'sender': sender
            }))
        except Exception as e:
            logger.error(f"Error in audio_message: {e}")

    async def video_signal(self, event):
        try:
            signal = event['signal']
            sender = event['sender']
            to = event.get('to')
            await self.send(text_data=json.dumps({
                'signal': signal,
                'sender': sender,
                'to': to
            }))
        except Exception as e:
            logger.error(f"Error in video_signal: {e}")

    async def candidate(self, event):
        try:
            candidate = event['candidate']
            sender = event['sender']
            to = event.get('to')
            await self.send(text_data=json.dumps({
                'type': 'candidate',
                'candidate': candidate,
                'sender': sender,
                'to': to
            }))
        except Exception as e:
            logger.error(f"Error in candidate: {e}")

    async def close_room(self, event):
        try:
            await self.close()
        except Exception as e:
            logger.error(f"Error in close_room: {e}")

    @database_sync_to_async
    def save_message(self, sender_email, receiver_email, message, is_group):
        try:
            User = get_user_model()
            sender = User.objects.get(email=sender_email)
            receiver = User.objects.get(email=receiver_email) if receiver_email else None
            task = None
            if is_group and self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = Task.objects.get(id=task_id)
            ChatMessage.objects.create(
                sender=sender,
                receiver=receiver,
                content=message,
                task=task,
                timestamp=timezone.now(),
                is_group=is_group
            )
        except Exception as e:
            logger.error(f"Error in save_message: {e}")

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user_email = None
            path = self.scope['path']
            if not path.startswith('/ws/video/'):
                await self.close()
                return
            self.room_name = path.split('/')[3]
            if not self.room_name:
                await self.close()
                return

            self.room_group_name = f'video_{self.room_name}'
            self.is_task_group = self.room_name.startswith('chat_task_')
            self.is_one_to_one = self.room_name.startswith('1v1_')

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            logger.debug(f"Connected to video room {self.room_name} (awaiting authentication)")
            await self.accept()
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
                if self.user_email:
                    logger.debug(f"Disconnected from video room {self.room_name} for user {self.user_email}")
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            logger.debug(f"Received raw data: {text_data}")

            if not self.user_email and text_data_json.get('type') == 'auth':
                self.user_email = text_data_json.get('user_email')
                if not self.user_email:
                    logger.warning("No user authentication provided")
                    await self.close()
                    return
                authenticated = await self.authenticate_user()
                if not authenticated:
                    logger.error(f"Authentication failed for user {self.user_email} in video room {self.room_name}")
                    await self.close()
                    return
                await self.send(json.dumps({
                    'type': 'auth_ack',
                    'status': 'authenticated',
                    'user': self.user_email
                }))
                return

            if not self.user_email:
                logger.warning("User not authenticated")
                await self.close()
                return

            signal = text_data_json.get('signal')
            audio_data = text_data_json.get('audio_data')
            candidate = text_data_json.get('candidate')

            if signal:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'video_signal',
                        'signal': signal,
                        'sender': self.user_email,
                        'to': text_data_json.get('to')
                    }
                )
            elif audio_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'audio_message',
                        'audio_data': audio_data,
                        'sender': self.user_email
                    }
                )
            elif candidate:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'candidate',
                        'candidate': candidate,
                        'sender': self.user_email,
                        'to': text_data_json.get('to')
                    }
                )
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in receive for video room {self.room_name}: {e}")
            await self.close()

    async def auth_ack(self, event):
        logger.debug(f"Received auth_ack for video room {self.room_name}")

    @database_sync_to_async
    def authenticate_user(self):
        try:
            if self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = Task.objects.get(id=task_id)
                if task.status in ['completed', 'cancelled']:
                    return False
                User = get_user_model()
                user = User.objects.get(email=self.user_email)
                return task.client == user or TaskApplication.objects.filter(task=task, volunteer=user, status='accepted').exists()
            elif self.is_one_to_one:
                try:
                    session = OneToOneChatSession.objects.get(room_name=self.room_name)
                    valid_emails = [session.user1.email, session.user2.email]
                    return self.user_email in valid_emails
                except OneToOneChatSession.DoesNotExist:
                    logger.error(f"OneToOneChatSession {self.room_name} not found")
                    return False
            return False
        except Exception as e:
            logger.error(f"Authentication error in video room {self.room_name}: {e}")
            return False

    async def video_signal(self, event):
        try:
            signal = event['signal']
            sender = event['sender']
            to = event.get('to')
            await self.send(text_data=json.dumps({
                'signal': signal,
                'sender': sender,
                'to': to
            }))
        except Exception as e:
            logger.error(f"Error in video_signal: {e}")

    async def audio_message(self, event):
        try:
            audio_data = event['audio_data']
            sender = event['sender']
            await self.send(text_data=json.dumps({
                'audio_data': audio_data,
                'sender': sender
            }))
        except Exception as e:
            logger.error(f"Error in audio_message: {e}")

    async def candidate(self, event):
        try:
            candidate = event['candidate']
            sender = event['sender']
            to = event.get('to')
            await self.send(text_data=json.dumps({
                'type': 'candidate',
                'candidate': candidate,
                'sender': sender,
                'to': to
            }))
        except Exception as e:
            logger.error(f"Error in candidate: {e}")