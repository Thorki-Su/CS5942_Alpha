from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from communication.models import ChatMessage, VideoCallSession, OneToOneChatSession
from communication.consumers import ChatConsumer, VideoCallConsumer
from task.models import Task, TaskApplication
from user.models import UserProfile
import json
import asyncio
from datetime import timedelta
from urllib.parse import urlencode

User = get_user_model()

class CommunicationModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='testpass123', role='client', is_active=True)
        self.user2 = User.objects.create_user(email='user2@example.com', password='testpass123', role='volunteer', is_active=True)
        self.user3 = User.objects.create_user(email='user3@example.com', password='testpass123', role='volunteer', is_active=True)
        self.user4 = User.objects.create_user(email='user4@example.com', password='testpass123', role='volunteer', is_active=True)
        UserProfile.objects.create(user=self.user1, first_name='User1', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user2, first_name='User2', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user3, first_name='User3', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user4, first_name='User4', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        self.task = Task.objects.create(
            client=self.user1,
            title='Test Task',
            description='Test Description',
            status='open',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=2),
            vol_number=2
        )
        self.pending_application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.user2,
            status='pending'
        )
        self.accepted_application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.user4,
            status='accepted'
        )

    def test_chat_message_creation(self):
        """测试ChatMessage模型的创建"""
        message = ChatMessage.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Hello, test message!',
            timestamp=timezone.now(),
            is_group=False,
            is_read=False
        )
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.receiver, self.user2)
        self.assertEqual(message.content, 'Hello, test message!')
        self.assertFalse(message.is_group)
        self.assertFalse(message.is_read)
        self.assertEqual(str(message), 'user1@example.com to user2@example.com: Hello, test message!')

    def test_video_call_session_creation(self):
        """测试VideoCallSession模型的创建"""
        session = VideoCallSession.objects.create(
            initiator=self.user1,
            participant=self.user2,
            task=self.task,
            start_time=timezone.now()
        )
        self.assertEqual(session.initiator, self.user1)
        self.assertEqual(session.participant, self.user2)
        self.assertEqual(session.task, self.task)
        self.assertEqual(str(session), 'user1@example.com with user2@example.com')

    def test_one_to_one_chat_session_creation(self):
        """测试OneToOneChatSession模型的创建"""
        session = OneToOneChatSession.objects.create(
            user1=self.user1,
            user2=self.user2,
            room_name='1v1_1_2'
        )
        self.assertEqual(session.user1, self.user1)
        self.assertEqual(session.user2, self.user2)
        self.assertEqual(session.room_name, '1v1_1_2')
        self.assertEqual(str(session), 'user1@example.com - user2@example.com (1v1_1_2)')

    def test_one_to_one_chat_session_unique_constraint(self):
        """测试OneToOneChatSession的唯一性约束"""
        OneToOneChatSession.objects.create(
            user1=self.user1,
            user2=self.user2,
            room_name='1v1_1_2'
        )
        with self.assertRaises(Exception):
            OneToOneChatSession.objects.create(
                user1=self.user1,
                user2=self.user2,
                room_name='1v1_1_2_duplicate'
            )

class CommunicationViewTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user1 = User.objects.create_user(email='user1@example.com', password='testpass123', role='client', is_active=True)
        self.user2 = User.objects.create_user(email='user2@example.com', password='testpass123', role='volunteer', is_active=True)
        self.user3 = User.objects.create_user(email='user3@example.com', password='testpass123', role='volunteer', is_active=True)
        self.user4 = User.objects.create_user(email='user4@example.com', password='testpass123', role='volunteer', is_active=True)
        UserProfile.objects.create(user=self.user1, first_name='User1', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user2, first_name='User2', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user3, first_name='User3', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user4, first_name='User4', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        self.task = Task.objects.create(
            client=self.user1,
            title='Test Task',
            description='Test Description',
            status='open',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=2),
            vol_number=2
        )
        self.pending_application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.user2,
            status='pending'
        )
        self.accepted_application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.user4,
            status='accepted'
        )

    def test_message_selection_view(self):
        """测试消息选择视图"""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('communication:message_selection'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/message_selection.html')

    def test_one_to_one_chat_selection_view(self):
        """测试1v1聊天用户选择视图"""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('communication:one_to_one_chat_selection'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/one_to_one_chat_selection.html')
        self.assertContains(response, 'user2@example.com')

    def test_task_communication_view_client(self):
        """测试任务发布者访问任务聊天室"""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('communication:task_communication_view', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/communication.html')
        self.assertEqual(response.context['room_name'], f'chat_task_{self.task.id}')
        self.assertEqual(response.context['user2_email'], 'Task Group Chat')
        self.assertIn('user1@example.com', response.context['participants'])
        self.assertIn('user4@example.com', response.context['participants'])

    def test_task_communication_view_accepted_volunteer(self):
        """测试接受的志愿者访问任务聊天室"""
        self.client.force_login(self.user4)
        response = self.client.get(reverse('communication:task_communication_view', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/communication.html')
        self.assertEqual(response.context['room_name'], f'chat_task_{self.task.id}')
        self.assertEqual(response.context['user2_email'], 'Task Group Chat')
        self.assertIn('user1@example.com', response.context['participants'])
        self.assertIn('user4@example.com', response.context['participants'])

    def test_task_communication_view_pending_volunteer(self):
        """测试pending志愿者无法访问任务聊天室"""
        self.client.force_login(self.user2)
        response = self.client.get(reverse('communication:task_communication_view', args=[self.task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user:home'))

    def test_task_communication_view_unauthorized(self):
        """测试无关用户无法访问任务聊天室"""
        self.client.force_login(self.user3)
        response = self.client.get(reverse('communication:task_communication_view', args=[self.task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user:home'))

    def test_task_communication_view_completed_task(self):
        """测试已完成任务的聊天室不可访问"""
        self.task.status = 'completed'
        self.task.save()
        self.client.force_login(self.user1)
        response = self.client.get(reverse('communication:task_communication_view', args=[self.task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user:home'))

    def test_create_one_to_one_room_volunteer_to_client(self):
        """测试志愿者与任务发布者创建1v1聊天室"""
        self.client.force_login(self.user2)
        self.client.get(reverse('communication:message_selection'))  # 触发CSRF令牌生成
        csrf_token = self.client.cookies.get('csrftoken', '').value
        response = self.client.post(
            reverse('communication:create_one_to_one_room'),
            data=urlencode({'user2_email': 'user1@example.com'}),
            content_type='application/x-www-form-urlencoded',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.content}")
        data = response.json()
        self.assertIn('room_name', data)
        self.assertIn('url', data)

    def test_create_one_to_one_room_invalid_email(self):
        """测试使用无效email创建1v1聊天室"""
        self.client.force_login(self.user2)
        self.client.get(reverse('communication:message_selection'))
        csrf_token = self.client.cookies.get('csrftoken', '').value
        response = self.client.post(
            reverse('communication:create_one_to_one_room'),
            data=urlencode({'user2_email': ''}),
            content_type='application/x-www-form-urlencoded',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}: {response.content}")
        self.assertEqual(response.json()['error'], 'Please enter a different valid email')

    def test_create_one_to_one_room_invalid_user(self):
        """测试使用不存在用户创建1v1聊天室"""
        self.client.force_login(self.user2)
        self.client.get(reverse('communication:message_selection'))
        csrf_token = self.client.cookies.get('csrftoken', '').value
        response = self.client.post(
            reverse('communication:create_one_to_one_room'),
            data=urlencode({'user2_email': 'invalid@example.com'}),
            content_type='application/x-www-form-urlencoded',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, 404, f"Expected 404, got {response.status_code}: {response.content}")
        self.assertEqual(response.json()['error'], 'User invalid@example.com not found or inactive: CustomUser matching query does not exist.')

class TaskDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(email='user1@example.com', password='testpass123', role='client', is_active=True)
        self.user2 = User.objects.create_user(email='user2@example.com', password='testpass123', role='volunteer', is_active=True)
        self.user3 = User.objects.create_user(email='user3@example.com', password='testpass123', role='volunteer', is_active=True)
        self.user4 = User.objects.create_user(email='user4@example.com', password='testpass123', role='volunteer', is_active=True)
        UserProfile.objects.create(user=self.user1, first_name='User1', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user2, first_name='User2', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user3, first_name='User3', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        UserProfile.objects.create(user=self.user4, first_name='User4', last_name='Test', phone_number='1234567890', location='AB12 3CD')
        self.task = Task.objects.create(
            client=self.user1,
            title='Test Task',
            description='Test Description',
            status='open',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=2),
            vol_number=2
        )
        self.pending_application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.user2,
            status='pending'
        )
        self.accepted_application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.user4,
            status='accepted'
        )

    def test_task_detail_view_client(self):
        """测试任务发布者查看任务详情"""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('task:task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Join Task Chat")
        self.assertNotContains(response, f"Chat with Task Creator ({self.user1.email})")

    def test_task_detail_view_pending_volunteer(self):
        """测试pending志愿者查看任务详情，显示1v1聊天入口"""
        self.client.force_login(self.user2)
        response = self.client.get(reverse('task:task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Chat with Task Creator ({self.user1.email})")
        self.assertNotContains(response, "Join Task Chat")

    def test_task_detail_view_accepted_volunteer(self):
        """测试accepted志愿者查看任务详情，显示任务聊天室入口"""
        self.client.force_login(self.user4)
        response = self.client.get(reverse('task:task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Join Task Chat")
        self.assertContains(response, f"Chat with Task Creator ({self.user1.email})")

    def test_task_detail_view_non_applied_volunteer(self):
        """测试未申请志愿者查看任务详情，显示1v1聊天入口"""
        self.client.force_login(self.user3)
        response = self.client.get(reverse('task:task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Chat with Task Creator ({self.user1.email})")
        self.assertNotContains(response, "Join Task Chat")

class ChatConsumerTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='testpass123', role='client', is_active=True)
        self.user2 = User.objects.create_user(email='user2@example.com', password='testpass123', role='volunteer', is_active=True)
        self.user3 = User.objects.create_user(email='user3@example.com', password='testpass123', role='volunteer', is_active=True)
        self.task = Task.objects.create(
            client=self.user1,
            title='Test Task',
            description='Test Description',
            status='open',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=2),
            vol_number=2
        )
        self.task_application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.user2,
            status='accepted'
        )
        self.session = OneToOneChatSession.objects.create(
            user1=self.user1,
            user2=self.user2,
            room_name='1v1_1_2'
        )

    async def test_chat_consumer_connect_and_auth(self):
        """测试ChatConsumer连接和认证"""
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/1v1_1_2/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({'type': 'auth', 'user_email': 'user1@example.com'})
        response = await communicator.receive_json_from(timeout=180)
        self.assertEqual(response['type'], 'auth_ack')
        self.assertEqual(response['status'], 'authenticated')
        await communicator.disconnect()

    async def test_chat_consumer_message(self):
        """测试ChatConsumer消息发送和接收"""
        communicator1 = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/1v1_1_2/")
        communicator2 = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/1v1_1_2/")
        await communicator1.connect()
        await communicator2.connect()
        await communicator1.send_json_to({'type': 'auth', 'user_email': 'user1@example.com'})
        await communicator1.receive_json_from(timeout=180)
        await communicator2.send_json_to({'type': 'auth', 'user_email': 'user2@example.com'})
        await communicator2.receive_json_from(timeout=180)
        await communicator1.send_json_to({'message': 'Hello from user1'})
        response = await communicator2.receive_json_from(timeout=180)
        self.assertEqual(response['message'], 'Hello from user1')
        self.assertEqual(response['sender'], 'user1@example.com')
        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_chat_consumer_unauthenticated(self):
        """测试ChatConsumer未认证连接"""
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/1v1_1_2/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({'message': 'Unauthorized message'})
        response = await communicator.receive_output(timeout=180)
        self.assertEqual(response['type'], 'websocket.close')
        await communicator.disconnect()

    async def test_task_chat_consumer_client(self):
        """测试任务发布者连接任务聊天室"""
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/chat_task_{self.task.id}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({'type': 'auth', 'user_email': 'user1@example.com'})
        response = await communicator.receive_json_from(timeout=180)
        self.assertEqual(response['type'], 'auth_ack')
        self.assertEqual(response['status'], 'authenticated')
        await communicator.disconnect()

    async def test_task_chat_consumer_accepted_volunteer(self):
        """测试接受的志愿者连接任务聊天室"""
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/chat_task_{self.task.id}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({'type': 'auth', 'user_email': 'user2@example.com'})
        response = await communicator.receive_json_from(timeout=180)
        self.assertEqual(response['type'], 'auth_ack')
        self.assertEqual(response['status'], 'authenticated')
        await communicator.disconnect()

    async def test_task_chat_consumer_unauthorized(self):
        """测试无关用户无法连接任务聊天室"""
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/chat_task_{self.task.id}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({'type': 'auth', 'user_email': 'user3@example.com'})
        response = await communicator.receive_output(timeout=180)
        self.assertEqual(response['type'], 'websocket.close')
        await communicator.disconnect()

    async def test_task_chat_message_broadcast(self):
        """测试任务聊天室消息广播"""
        communicator1 = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/chat_task_{self.task.id}/")
        communicator2 = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/chat_task_{self.task.id}/")
        await communicator1.connect()
        await communicator2.connect()
        await communicator1.send_json_to({'type': 'auth', 'user_email': 'user1@example.com'})
        await communicator1.receive_json_from(timeout=180)
        await communicator2.send_json_to({'type': 'auth', 'user_email': 'user2@example.com'})
        await communicator2.receive_json_from(timeout=180)
        await communicator1.send_json_to({'message': 'Task group message'})
        response = await communicator2.receive_json_from(timeout=180)
        self.assertEqual(response['message'], 'Task group message')
        self.assertEqual(response['sender'], 'user1@example.com')
        self.assertTrue(response['is_group'])
        message = await database_sync_to_async(ChatMessage.objects.filter(content='Task group message').first)()
        self.assertIsNotNone(message)
        task = await database_sync_to_async(lambda: message.task)()
        self.assertEqual(task, self.task)
        self.assertTrue(message.is_group)
        await communicator1.disconnect()
        await communicator2.disconnect()

class VideoCallConsumerTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='testpass123', role='client', is_active=True)
        self.user2 = User.objects.create_user(email='user2@example.com', password='testpass123', role='volunteer', is_active=True)
        self.session = OneToOneChatSession.objects.create(
            user1=self.user1,
            user2=self.user2,
            room_name='1v1_1_2'
        )

    async def test_video_call_consumer_connect_and_auth(self):
        """测试VideoCallConsumer连接和认证"""
        communicator = WebsocketCommunicator(VideoCallConsumer.as_asgi(), "/ws/video/1v1_1_2/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({'type': 'auth', 'user_email': 'user1@example.com'})
        response = await communicator.receive_json_from(timeout=180)
        self.assertEqual(response['type'], 'auth_ack')
        self.assertEqual(response['status'], 'authenticated')
        await communicator.disconnect()

    async def test_video_call_consumer_signal(self):
        """测试VideoCallConsumer信令处理"""
        communicator1 = WebsocketCommunicator(VideoCallConsumer.as_asgi(), "/ws/video/1v1_1_2/")
        communicator2 = WebsocketCommunicator(VideoCallConsumer.as_asgi(), "/ws/video/1v1_1_2/")
        await communicator1.connect()
        await communicator2.connect()
        await communicator1.send_json_to({'type': 'auth', 'user_email': 'user1@example.com'})
        await communicator1.receive_json_from(timeout=180)
        await communicator2.send_json_to({'type': 'auth', 'user_email': 'user2@example.com'})
        await communicator2.receive_json_from(timeout=180)
        await communicator1.send_json_to({
            'signal': {'type': 'offer', 'sdp': 'test_sdp'},
            'to': 'user2@example.com',
            'sender': 'user1@example.com'
        })
        response = await communicator2.receive_json_from(timeout=180)
        self.assertEqual(response['signal']['type'], 'offer')
        self.assertEqual(response['sender'], 'user1@example.com')
        await communicator1.disconnect()
        await communicator2.disconnect()