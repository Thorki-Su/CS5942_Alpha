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
import time

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user_email = None
            path = self.scope['path']
            if not path.startswith('/ws/chat/') and not path.startswith('/ws/user/'):
                await self.close()
                return
            if path.startswith('/ws/user/'):
                self.user_email = path.split('/')[3].replace('_', '@')
                self.user_channel_name = f'user_{self.user_email.replace("@", "_")}'
                await self.channel_layer.group_add(self.user_channel_name, self.channel_name)
                logger.debug(f"Connected to user channel {self.user_channel_name} (awaiting authentication)")
            else:
                self.room_name = path.split('/')[3]
                self.room_group_name = f'chat_{self.room_name}'
                self.is_task_group = self.room_name.startswith('chat_task_')
                self.is_one_to_one = self.room_name.startswith('1v1_')
                self.user_channel_name = f'user_{self.scope["user"].email.replace("@", "_")}'
                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                await self.channel_layer.group_add(self.user_channel_name, self.channel_name)
                logger.debug(f"Connected to {self.room_name} (awaiting authentication)")
            await self.accept()
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            if hasattr(self, 'user_channel_name'):
                await self.channel_layer.group_discard(self.user_channel_name, self.channel_name)
            logger.debug(f"Disconnected from {getattr(self, 'room_name', 'unknown') or getattr(self, 'user_channel_name', 'unknown')} with code {close_code}")
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            logger.debug(f"Received raw data: {text_data}")
            if text_data_json.get('type') == 'ping':
                await self.send(json.dumps({'type': 'pong'}))
                return
            if not self.user_email and text_data_json.get('type') == 'auth':
                self.user_email = text_data_json.get('user_email')
                if not self.user_email:
                    logger.warning("No user authentication provided")
                    await self.close()
                    return
                authenticated = await self.authenticate_user()
                logger.debug(f"Authentication result for {self.user_email}: {authenticated}")
                if not authenticated:
                    logger.error(f"Authentication failed for user {self.user_email} in room {getattr(self, 'room_name', 'unknown')}")
                    await self.close()
                    return
                await self.send(json.dumps({'type': 'auth_ack', 'status': 'authenticated', 'user': self.user_email}))
                logger.debug(f"Authenticated user {self.user_email} in room {getattr(self, 'room_name', 'unknown')}")

            if not self.user_email:
                logger.warning("User not authenticated, closing connection")
                await self.close()
                return

            message = text_data_json.get('message')
            audio_data = text_data_json.get('audio_data')
            signal = text_data_json.get('signal')
            candidate = text_data_json.get('candidate')

            if message:
                start_time = time.time()
                receiver = await self.get_receiver()
                logger.debug(f"Got receiver {receiver} in {time.time() - start_time:.3f}s")
                timestamp = timezone.now().isoformat()
                data = {
                    'message': message,
                    'sender': self.user_email,
                    'receiver': receiver,
                    'timestamp': timestamp,
                    'is_group': self.is_task_group
                }
                save_task = asyncio.create_task(self.save_message(self.user_email, receiver, message, self.is_task_group))
                save_task.add_done_callback(lambda t: logger.error(f"Save message task failed: {t.exception()}") if t.exception() else None)
                try:
                    await self.send(text_data=json.dumps(data))
                    logger.debug(f"Sending group message to {self.room_group_name}")
                    await self.channel_layer.group_send(self.room_group_name, {
                        'type': 'chat_message',
                        'message': message,
                        'sender': self.user_email,
                        'receiver': receiver,
                        'timestamp': timestamp,
                        'is_group': self.is_task_group
                    })
                    # Send unread notification
                    if self.is_one_to_one and receiver:
                        await self.channel_layer.group_send(
                            f'user_{receiver.replace("@", "_")}',
                            {
                                'type': 'unread_notification',
                                'sender': self.user_email,
                                'room_name': self.room_name,
                                'is_group': False
                            }
                        )
                    elif self.is_task_group:
                        task_id = self.room_name.split('_')[2]
                        participants = await self.get_task_participants(task_id)
                        for participant in participants:
                            if participant != self.user_email:
                                await self.channel_layer.group_send(
                                    f'user_{participant.replace("@", "_")}',
                                    {
                                        'type': 'unread_notification',
                                        'sender': self.user_email,
                                        'room_name': self.room_name,
                                        'is_group': True,
                                        'task_id': task_id
                                    }
                                )
                    logger.debug(f"Group send completed in {time.time() - start_time:.3f}s")
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
            logger.error(f"Unexpected error in receive for room {getattr(self, 'room_name', 'unknown')}: {e}")
            await self.close()

    @database_sync_to_async
    def save_message(self, sender_email, receiver_email, message, is_group):
        try:
            User = get_user_model()
            sender = User.objects.get(email=sender_email)
            receiver = User.objects.get(email=receiver_email) if receiver_email else None
            task = None
            if is_group:
                task_id = self.room_name.split('_')[2]
                task = Task.objects.get(id=task_id)
            ChatMessage.objects.create(
                sender=sender,
                receiver=receiver,
                content=message,
                task=task,
                is_group=is_group,
                is_read=False
            )
            logger.debug(f"Saved message from {sender_email} to {receiver_email or 'group'}")
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise

    @database_sync_to_async
    def authenticate_user(self):
        try:
            if hasattr(self, 'is_task_group') and self.is_task_group:
                task_id = int(self.room_name.split('_')[2])
                task = Task.objects.get(id=task_id)
                if task.status in ['completed', 'cancelled']:
                    return False
                User = get_user_model()
                user = User.objects.get(email=self.user_email)
                return task.client == user or TaskApplication.objects.filter(task=task, volunteer=user, status='accepted').exists()
            elif hasattr(self, 'is_one_to_one') and self.is_one_to_one:
                try:
                    session = OneToOneChatSession.objects.get(room_name=self.room_name)
                    valid_emails = [session.user1.email, session.user2.email]
                    return self.user_email in valid_emails
                except OneToOneChatSession.DoesNotExist:
                    logger.error(f"OneToOneChatSession {self.room_name} not found")
                    return False
            elif self.scope['path'].startswith('/ws/user/'):  # 用户通知路径，无需房间认证
                return True  # 只需auth user_email
            return False
        except (ValueError, ObjectDoesNotExist) as e:
            logger.error(f"Authentication error in room {getattr(self, 'room_name', 'unknown')}: {e}")
            return False
        except Exception as e:
            logger.error(f"Authentication error in room {getattr(self, 'room_name', 'unknown')}: {e}")
            return False

    @database_sync_to_async
    def get_receiver(self):
        start_time = time.time()
        try:
            if hasattr(self, 'is_one_to_one') and self.is_one_to_one:
                session = OneToOneChatSession.objects.get(room_name=self.room_name)
                if self.user_email == session.user1.email:
                    result = session.user2.email
                elif self.user_email == session.user2.email:
                    result = session.user1.email
                else:
                    result = None
                logger.debug(f"Got receiver {result} in {time.time() - start_time:.3f}s")
                return result
            logger.debug(f"No receiver for group chat in {time.time() - start_time:.3f}s")
            return None
        except OneToOneChatSession.DoesNotExist:
            logger.error(f"OneToOneChatSession {self.room_name} not found")
            return None

    @database_sync_to_async
    def get_task_participants(self, task_id):
        task = Task.objects.get(id=task_id)
        return [task.client.email] + list(TaskApplication.objects.filter(
            task=task, status='accepted').values_list('volunteer__email', flat=True))

    async def chat_message(self, event):
        try:
            message = event['message']
            sender = event['sender']
            receiver = event.get('receiver')
            timestamp = event.get('timestamp')
            is_group = event.get('is_group', False)
            start_time = time.time()
            await self.send(text_data=json.dumps({
                'message': message,
                'sender': sender,
                'receiver': receiver,
                'timestamp': timestamp,
                'is_group': is_group
            }))
            logger.debug(f"Sent chat_message to {self.user_email} in {time.time() - start_time:.3f}s")
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

    async def unread_notification(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'unread_notification',
                'sender': event['sender'],
                'room_name': event['room_name'],
                'is_group': event['is_group'],
                'task_id': event.get('task_id')
            }))
        except Exception as e:
            logger.error(f"Error in unread_notification: {e}")

    async def friend_request_notification(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'friend_request_notification',
                'from_email': event['from_email'],
                'request_id': event['request_id']
            }))
        except Exception as e:
            logger.error(f"Error in friend_request_notification: {e}")

    async def friend_update_notification(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'friend_update_notification',
                'from_email': event['from_email'],
                'status': event['status']  # 'accepted' or 'rejected'
            }))
        except Exception as e:
            logger.error(f"Error in friend_update_notification: {e}")