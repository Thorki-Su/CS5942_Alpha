# communication/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.paginator import Paginator
from django.test.utils import override_settings
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
import json
import asyncio

from .models import ChatMessage, VideoCallSession, OneToOneChatSession
from .views import get_or_create_one_to_one_room
from .consumers import ChatConsumer, VideoCallConsumer
from user.models import UserProfile, ClientProfile, VolunteerProfile
from task.models import Task, TaskApplication, SupportType

User = get_user_model()


@override_settings(
    STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage',
    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage'
)
class CommunicationModelsTests(TestCase):
    def setUp(self):
        # Create users
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        # Create user profiles
        self.client_profile = UserProfile.objects.create(
            user=self.client_user,
            first_name='Client',
            last_name='Test',
            phone_number='1234567890',
            location='AB25 3DD'
        )
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='Volunteer',
            last_name='Test',
            phone_number='0987654321',
            location='AB25 3DD'
        )
        
        # Create specific profiles
        ClientProfile.objects.create(
            user_profile=self.client_profile,
            preferred_contact_method='email'
        )
        VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )
        
        # Create support type and task
        self.support_type = SupportType.objects.create(name='Medical Assistance')
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=2),
            vol_number=1,
            client=self.client_user
        )
        self.task.work_area.add(self.support_type)

    # def test_chat_message_creation(self):
    #     """Test ChatMessage model creation and string representation"""
    #     message = ChatMessage.objects.create(
    #         sender=self.client_user,
    #         receiver=self.volunteer_user,
    #         content='Hello, this is a test message',
    #         task=self.task
    #     )
        
    #     self.assertEqual(message.sender, self.client_user)
    #     self.assertEqual(message.receiver, self.volunteer_user)
    #     self.assertEqual(message.content, 'Hello, this is a test message')
    #     self.assertEqual(message.task, self.task)
    #     self.assertIsNotNone(message.timestamp)
        
    #     # Test string representation
    #     expected_str = f"{self.client_user.email} to {self.volunteer_user.email}: Hello, this is a test"
    #     self.assertEqual(str(message), expected_str)

    def test_chat_message_group_message(self):
        """Test ChatMessage for group messages (no receiver)"""
        message = ChatMessage.objects.create(
            sender=self.client_user,
            receiver=None,
            content='Group message',
            task=self.task
        )
        
        self.assertEqual(message.sender, self.client_user)
        self.assertIsNone(message.receiver)
        self.assertEqual(message.task, self.task)
        
        # Test string representation for group message
        expected_str = f"{self.client_user.email} to group: Group message"
        self.assertEqual(str(message), expected_str)

    def test_video_call_session_creation(self):
        """Test VideoCallSession model creation and string representation"""
        call_session = VideoCallSession.objects.create(
            initiator=self.client_user,
            participant=self.volunteer_user,
            task=self.task
        )
        
        self.assertEqual(call_session.initiator, self.client_user)
        self.assertEqual(call_session.participant, self.volunteer_user)
        self.assertEqual(call_session.task, self.task)
        self.assertIsNotNone(call_session.start_time)
        self.assertIsNone(call_session.end_time)
        
        # Test string representation
        expected_str = f"{self.client_user.email} with {self.volunteer_user.email}"
        self.assertEqual(str(call_session), expected_str)

    def test_video_call_session_group_call(self):
        """Test VideoCallSession for group calls (no participant)"""
        call_session = VideoCallSession.objects.create(
            initiator=self.client_user,
            participant=None,
            task=self.task
        )
        
        self.assertEqual(call_session.initiator, self.client_user)
        self.assertIsNone(call_session.participant)
        
        # Test string representation for group call
        expected_str = f"{self.client_user.email} with group"
        self.assertEqual(str(call_session), expected_str)

    def test_one_to_one_chat_session_creation(self):
        """Test OneToOneChatSession model creation and constraints"""
        session = OneToOneChatSession.objects.create(
            user1=self.client_user,
            user2=self.volunteer_user,
            room_name='1v1_1_2'
        )
        
        self.assertEqual(session.user1, self.client_user)
        self.assertEqual(session.user2, self.volunteer_user)
        self.assertEqual(session.room_name, '1v1_1_2')
        self.assertIsNotNone(session.created_at)
        
        # Test string representation
        expected_str = f"{self.client_user.email} - {self.volunteer_user.email} (1v1_1_2)"
        self.assertEqual(str(session), expected_str)

    def test_one_to_one_chat_session_unique_constraint(self):
        """Test unique constraint on OneToOneChatSession"""
        # Create first session
        OneToOneChatSession.objects.create(
            user1=self.client_user,
            user2=self.volunteer_user,
            room_name='1v1_1_2'
        )
        
        # Try to create duplicate session - should raise IntegrityError
        with self.assertRaises(Exception):
            OneToOneChatSession.objects.create(
                user1=self.client_user,
                user2=self.volunteer_user,
                room_name='1v1_1_2_duplicate'
            )


@override_settings(
    STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage',
    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage'
)
class CommunicationViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        # Create user profiles
        for user, role in [(self.client_user, 'client'), (self.volunteer_user, 'volunteer'), (self.other_user, 'volunteer')]:
            profile = UserProfile.objects.create(
                user=user,
                first_name=role.capitalize(),
                last_name='Test',
                phone_number='1234567890',
                location='AB25 3DD'
            )
            if role == 'client':
                ClientProfile.objects.create(
                    user_profile=profile,
                    preferred_contact_method='email'
                )
            else:
                VolunteerProfile.objects.create(
                    user_profile=profile,
                    university_course='Computer Science',
                    profession='Student'
                )
        
        # Create support type and task
        self.support_type = SupportType.objects.create(name='Medical Assistance')
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=2),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        self.task.work_area.add(self.support_type)
        
        # Create task application
        self.task_application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='accepted'
        )

    def test_message_selection_view_authenticated(self):
        """Test message selection view for authenticated user"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:message_selection'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/message_selection.html')

    def test_message_selection_view_unauthenticated(self):
        """Test message selection view redirects for unauthenticated user"""
        response = self.client.get(reverse('communication:message_selection'))
        self.assertRedirects(response, '/login/?next=/communication/')

    def test_one_to_one_chat_selection_view(self):
        """Test one-to-one chat selection view"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:one_to_one_chat_selection'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/one_to_one_chat_selection.html')
        self.assertIn('users', response.context)
        
        # Should exclude current user
        users = response.context['users']
        user_emails = [user.email for user in users]
        self.assertNotIn('client@test.com', user_emails)
        self.assertIn('volunteer@test.com', user_emails)
        self.assertIn('other@test.com', user_emails)

    def test_one_to_one_chat_selection_view_with_search(self):
        """Test one-to-one chat selection view with search query"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:one_to_one_chat_selection'), {'q': 'volunteer'})
        
        self.assertEqual(response.status_code, 200)
        users = response.context['users']
        user_emails = [user.email for user in users]
        self.assertIn('volunteer@test.com', user_emails)
        self.assertNotIn('other@test.com', user_emails)

    def test_one_to_one_chat_selection_view_pagination(self):
        """Test pagination in one-to-one chat selection view"""
        # Create more users to test pagination
        for i in range(15):
            User.objects.create_user(
                email=f'user{i}@test.com',
                password='testpass123',
                role='volunteer',
                is_active=True
            )
        
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:one_to_one_chat_selection'))
        
        self.assertEqual(response.status_code, 200)
        users = response.context['users']
        self.assertEqual(len(users), 10)  # Should be paginated to 10 per page
        self.assertTrue(users.has_next())

    def test_task_communication_view_authorized_client(self):
        """Test task communication view for authorized client"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:task_communication_view', args=[self.task.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/communication.html')
        self.assertEqual(response.context['room_name'], f'chat_task_{self.task.id}')

    def test_task_communication_view_authorized_volunteer(self):
        """Test task communication view for authorized volunteer"""
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('communication:task_communication_view', args=[self.task.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/communication.html')
        self.assertEqual(response.context['room_name'], f'chat_task_{self.task.id}')

    def test_task_communication_view_unauthorized(self):
        """Test task communication view for unauthorized user"""
        self.client.login(email='other@test.com', password='testpass123')
        response = self.client.get(reverse('communication:task_communication_view', args=[self.task.id]))
        
        self.assertRedirects(response, reverse('user:home'))

    def test_group_chats_view(self):
        """Test group chats view"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:group_chats'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/task_chats.html')
        self.assertIn('tasks', response.context)
        
        # Should only show open tasks
        tasks = response.context['tasks']
        for task in tasks:
            self.assertEqual(task.status, 'open')

    def test_one_to_one_communication_view(self):
        """Test one-to-one communication view"""
        # Create a chat session
        session = OneToOneChatSession.objects.create(
            user1=self.client_user,
            user2=self.volunteer_user,
            room_name='1v1_1_2'
        )
        
        # Create some messages
        ChatMessage.objects.create(
            sender=self.client_user,
            receiver=self.volunteer_user,
            content='Hello'
        )
        ChatMessage.objects.create(
            sender=self.volunteer_user,
            receiver=self.client_user,
            content='Hi there'
        )
        
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:one_to_one_communication_view', args=[session.room_name]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'communication/communication.html')
        self.assertEqual(response.context['room_name'], session.room_name)
        self.assertEqual(response.context['user2_email'], 'volunteer@test.com')
        self.assertEqual(len(response.context['messages']), 2)

    def test_create_one_to_one_room_success(self):
        """Test successful creation of one-to-one room"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('communication:create_one_to_one_room'), {
            'user2_email': 'volunteer@test.com'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('room_name', data)
        self.assertIn('url', data)
        
        # Check that session was created
        self.assertTrue(OneToOneChatSession.objects.filter(
            user1__email__in=['client@test.com', 'volunteer@test.com'],
            user2__email__in=['client@test.com', 'volunteer@test.com']
        ).exists())

    def test_create_one_to_one_room_get_method(self):
        """Test create one-to-one room with GET method (should fail)"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:create_one_to_one_room'))
        
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertEqual(data['error'], 'Method not allowed')

    def test_create_one_to_one_room_same_user(self):
        """Test create one-to-one room with same user (should fail)"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('communication:create_one_to_one_room'), {
            'user2_email': 'client@test.com'
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'Please enter a different valid email')

    def test_create_one_to_one_room_nonexistent_user(self):
        """Test create one-to-one room with nonexistent user"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('communication:create_one_to_one_room'), {
            'user2_email': 'nonexistent@test.com'
        })
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('not found or inactive', data['error'])

    def test_create_one_to_one_room_existing_session(self):
        """Test create one-to-one room when session already exists"""
        # Create existing session
        existing_session = OneToOneChatSession.objects.create(
            user1=self.client_user,
            user2=self.volunteer_user,
            room_name='1v1_1_2'
        )
        
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('communication:create_one_to_one_room'), {
            'user2_email': 'volunteer@test.com'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['room_name'], existing_session.room_name)


@override_settings(
    STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage',
    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage'
)
class CommunicationUtilsTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )

    # def test_get_or_create_one_to_one_room_new_session(self):
    #     """Test creating new one-to-one room session"""
    #     import asyncio
        
    #     async def test_async():
    #         room_name = await get_or_create_one_to_one_room('client@test.com', 'volunteer@test.com')
    #         self.assertTrue(room_name.startswith('1v1_'))
            
    #         # Check that session was created
    #         session = await database_sync_to_async(OneToOneChatSession.objects.get)(room_name=room_name)
    #         self.assertIsNotNone(session)
        
    #     asyncio.run(test_async())

    # def test_get_or_create_one_to_one_room_existing_session(self):
    #     """Test getting existing one-to-one room session"""
    #     # Create existing session
    #     existing_session = OneToOneChatSession.objects.create(
    #         user1=self.client_user,
    #         user2=self.volunteer_user,
    #         room_name='1v1_1_2'
    #     )
        
    #     import asyncio
        
    #     async def test_async():
    #         room_name = await get_or_create_one_to_one_room('client@test.com', 'volunteer@test.com')
    #         self.assertEqual(room_name, existing_session.room_name)
        
    #     asyncio.run(test_async())

    # def test_get_or_create_one_to_one_room_nonexistent_user(self):
    #     """Test get_or_create_one_to_one_room with nonexistent user"""
    #     import asyncio
        
    #     async def test_async():
    #         with self.assertRaises(User.DoesNotExist):
    #             await get_or_create_one_to_one_room('client@test.com', 'nonexistent@test.com')
        
    #     asyncio.run(test_async())


# Note: WebSocket consumer tests would require additional setup with channels testing
# and are more complex to implement. They would test the ChatConsumer and VideoCallConsumer
# functionality including connection, message handling, and disconnection.
# For now, we focus on the synchronous parts of the application.

class CommunicationIntegrationTests(TestCase):
    """Integration tests for communication workflows"""
    
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        # Create user profiles
        for user, role in [(self.client_user, 'client'), (self.volunteer_user, 'volunteer')]:
            profile = UserProfile.objects.create(
                user=user,
                first_name=role.capitalize(),
                last_name='Test',
                phone_number='1234567890',
                location='AB25 3DD'
            )
            if role == 'client':
                ClientProfile.objects.create(
                    user_profile=profile,
                    preferred_contact_method='email'
                )
            else:
                VolunteerProfile.objects.create(
                    user_profile=profile,
                    university_course='Computer Science',
                    profession='Student'
                )

    def test_complete_one_to_one_chat_workflow(self):
        """Test complete workflow of creating and accessing one-to-one chat"""
        self.client.login(email='client@test.com', password='testpass123')
        
        # Step 1: Access chat selection page
        response = self.client.get(reverse('communication:one_to_one_chat_selection'))
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Create one-to-one room
        response = self.client.post(reverse('communication:create_one_to_one_room'), {
            'user2_email': 'volunteer@test.com'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        room_name = data['room_name']
        
        # Step 3: Access the created room
        response = self.client.get(reverse('communication:one_to_one_communication_view', args=[room_name]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['room_name'], room_name)
        self.assertEqual(response.context['user2_email'], 'volunteer@test.com')

    def test_task_communication_workflow(self):
        """Test complete workflow of task-based communication"""
        # Create task and application
        support_type = SupportType.objects.create(name='Medical Assistance')
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=2),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        task.work_area.add(support_type)
        
        TaskApplication.objects.create(
            task=task,
            volunteer=self.volunteer_user,
            status='accepted'
        )
        
        # Test client access
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('communication:task_communication_view', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        
        # Test volunteer access
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('communication:task_communication_view', args=[task.id]))
        self.assertEqual(response.status_code, 200)