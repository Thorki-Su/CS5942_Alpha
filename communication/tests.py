import asyncio
from asgiref.sync import sync_to_async
from django.test import TestCase, AsyncTestCase
from django.urls import reverse
from channels.testing import WebsocketCommunicator
from communication.consumers import ChatConsumer, VideoCallConsumer
from communication.models import ChatMessage, VideoCallSession
from django.contrib.auth import get_user_model
from task.models import Task, TaskApplication
import json
from final_project.asgi import application
import django

django.setup()

User = get_user_model()

@sync_to_async
def create_user(email, password, role):
    return User.objects.create_user(email=email, password=password, role=role)

@sync_to_async
def create_task_and_application(client, volunteer):
    with django.db.connection.cursor() as cursor:
        cursor.execute("PRAGMA busy_timeout = 10000")  # 10秒超时
    task = Task.objects.create(
        title="Test Task",
        description="Test Description",
        start_time="2025-07-17 10:00:00+00:00",
        end_time="2025-07-17 12:00:00+00:00",
        vol_number=1,
        status="open",
        client=client
    )
    TaskApplication.objects.create(task=task, volunteer=volunteer, status="accepted")
    return task

class CommunicationModelTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@test.com", password="testpass123", role="client")
        self.volunteer_user = User.objects.create_user(email="volunteer@test.com", password="testpass123", role="volunteer")

    def test_chat_message_creation(self):
        message = ChatMessage.objects.create(
            sender=self.client_user,
            receiver=self.volunteer_user,
            content="Hello, Volunteer!",
            task=None
        )
        self.assertEqual(message.content, "Hello, Volunteer!")
        self.assertEqual(str(message), f"{self.client_user.email} to {self.volunteer_user.email}: Hello, Volu")

    def test_video_call_session_creation(self):
        session = VideoCallSession.objects.create(
            initiator=self.client_user,
            participant=self.volunteer_user,
            task=None
        )
        self.assertEqual(session.initiator, self.client_user)
        self.assertEqual(str(session), f"{self.client_user.email} with {self.volunteer_user.email}")

class CommunicationConsumerTests(AsyncTestCase):
    async def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.client = await create_user("client@test.com", "testpass123", "client")
        self.volunteer = await create_user("volunteer@test.com", "testpass123", "volunteer")
        self.task = await create_task_and_application(self.client, self.volunteer)

    async def test_chat_consumer_connect(self):
        communicator = WebsocketCommunicator(application, f"/ws/chat/chat_task_{self.task.id}/")
        communicator.scope["user"] = self.client
        connected, subprotocol = await communicator.connect()
        print(f"ChatConsumer connected: {connected}")  # 调试输出
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_chat_consumer_message(self):
        communicator = WebsocketCommunicator(application, f"/ws/chat/chat_task_{self.task.id}/")
        communicator.scope["user"] = self.client
        connected, subprotocol = await communicator.connect()
        print(f"ChatConsumer connected: {connected}")
        self.assertTrue(connected)

        await communicator.send_json_to({"message": "Test Message"})
        response = await communicator.receive_json_from()
        self.assertEqual(response["message"], "Test Message")
        self.assertEqual(response["sender"], "client@test.com")

        await communicator.disconnect()

    async def test_video_call_consumer_connect(self):
        communicator = WebsocketCommunicator(application, f"/ws/video/chat_task_{self.task.id}/")
        communicator.scope["user"] = self.client
        connected, subprotocol = await communicator.connect()
        print(f"VideoCallConsumer connected: {connected}")
        self.assertTrue(connected)
        await communicator.disconnect()

class CommunicationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.client_user = User.objects.create_user(email="client@test.com", password="testpass123", role="client")
        self.volunteer_user = User.objects.create_user(email="volunteer@test.com", password="testpass123", role="volunteer")
        self.client.login(email="client@test.com", password="testpass123")

    def test_communication_view(self):
        response = self.client.get(reverse("communication:communication_view"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "communication/communication.html")

    def test_task_communication_view(self):
        task = Task.objects.create(
            title="Test Task",
            description="Test Description",
            start_time="2025-07-17 10:00:00+00:00",
            end_time="2025-07-17 12:00:00+00:00",
            vol_number=1,
            status="open",
            client=self.client_user
        )
        response = self.client.get(reverse("communication:task_communication_view", args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "communication/communication.html")

    def test_group_chats_view(self):
        response = self.client.get(reverse("communication:group_chats"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "communication/group_chats.html")