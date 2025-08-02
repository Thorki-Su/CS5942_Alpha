from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import HttpResponseForbidden
from unittest.mock import patch, Mock
from datetime import datetime, timedelta, time
from decimal import Decimal

from user.models import UserProfile, ClientProfile, VolunteerProfile, SupportType
from .models import Task, TaskApplication, TaskTemplate, TaskRecord, Feedback, StarRelation
from .forms import TaskForm, TaskFilterForm, TaskRecordForm, FeedbackForm

User = get_user_model()


class TaskModelTests(TestCase):
    """Test cases for Task model and related models"""
    
    def setUp(self):
        # Create test users
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
            first_name='Jane',
            last_name='Client',
            phone_number='1234567890',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='0987654321',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        
        # Create client and volunteer profiles
        ClientProfile.objects.create(
            user_profile=self.client_profile,
            preferred_contact_method='email'
        )
        VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )
        
        # Create support types
        self.support_type = SupportType.objects.create(name='Shopping')
        
        # Create test task
        self.task = Task.objects.create(
            title='Help with groceries',
            description='Need help with weekly shopping',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            vol_number=2,
            client=self.client_user,
            status='open'
        )
        self.task.work_area.add(self.support_type)

    def test_task_creation(self):
        """Test task creation with basic attributes"""
        self.assertEqual(self.task.title, 'Help with groceries')
        self.assertEqual(self.task.client, self.client_user)
        self.assertEqual(self.task.vol_number, 2)
        self.assertEqual(self.task.status, 'open')
        self.assertTrue(self.task.work_area.filter(name='Shopping').exists())

    def test_task_str_method(self):
        """Test task string representation"""
        expected = f"Help with groceries ({self.client_user.email})"
        self.assertEqual(str(self.task), expected)

    def test_task_is_active_property(self):
        """Test task is_active property"""
        self.assertTrue(self.task.is_active)
        
        self.task.status = 'completed'
        self.assertFalse(self.task.is_active)

    def test_task_is_closed_property(self):
        """Test task is_closed property"""
        self.assertFalse(self.task.is_closed)
        
        self.task.status = 'completed'
        self.assertTrue(self.task.is_closed)

    def test_task_is_ongoing_property(self):
        """Test task is_ongoing property"""
        self.assertFalse(self.task.is_ongoing)
        
        self.task.status = 'ongoing'
        self.assertTrue(self.task.is_ongoing)

    def test_task_is_within_24h(self):
        """Test task is_within_24h method"""
        # Task starts in 1 day, so not within 24h
        self.assertFalse(self.task.is_within_24h())
        
        # Change to start in 12 hours
        self.task.start_time = timezone.now() + timedelta(hours=12)
        self.task.save()
        self.assertTrue(self.task.is_within_24h())

    def test_task_cancel(self):
        """Test task cancellation"""
        self.task.cancel()
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'cancelled')
        self.assertIsNotNone(self.task.closed_at)

    def test_update_status_if_full(self):
        """Test task status update when applications reach vol_number"""
        # Create applications
        TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='accepted'
        )
        
        # Create another volunteer and application
        volunteer2 = User.objects.create_user(
            email='volunteer2@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        TaskApplication.objects.create(
            task=self.task,
            volunteer=volunteer2,
            status='accepted'
        )
        
        self.task.update_status_if_full()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'selected')


class TaskViewTests(TestCase):
    """Test cases for Task views"""
    
    def setUp(self):
        # Create test users
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
            first_name='Jane',
            last_name='Client',
            phone_number='1234567890',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='0987654321',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        
        # Create client and volunteer profiles
        ClientProfile.objects.create(
            user_profile=self.client_profile,
            preferred_contact_method='email'
        )
        VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )
        
        # Create support type
        self.support_type = SupportType.objects.create(name='Shopping')
        
        # Create test task
        self.task = Task.objects.create(
            title='Help with groceries',
            description='Need help with weekly shopping',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        self.task.work_area.add(self.support_type)
        
        self.client = Client()

    def test_mytask_view_client_access(self):
        """Test that clients can access their task list"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('task:mytask'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Help with groceries')

    def test_mytask_view_volunteer_forbidden(self):
        """Test that volunteers cannot access client task list"""
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('task:mytask'))
        
        self.assertEqual(response.status_code, 403)

    def test_task_detail_view(self):
        """Test task detail view accessibility"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('task:task_detail', args=[self.task.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Help with groceries')
        self.assertContains(response, 'Need help with weekly shopping')

    def test_task_create_view_get(self):
        """Test task creation form display"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('task:task_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'title')
        self.assertContains(response, 'description')

    def test_task_create_view_post_valid(self):
        """Test successful task creation"""
        self.client.login(email='client@test.com', password='testpass123')
        
        task_data = {
            'title': 'New Test Task',
            'description': 'Test description',
            'start_time': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': (timezone.now() + timedelta(days=2, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'vol_number': 1,
            'work_area': [self.support_type.id]
        }
        
        response = self.client.post(reverse('task:task_create'), task_data)
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(Task.objects.filter(title='New Test Task').exists())

    def test_tasklist_view_volunteer_access(self):
        """Test that volunteers can access task list"""
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('task:tasklist'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Help with groceries')

    def test_tasklist_view_client_forbidden(self):
        """Test that clients cannot access volunteer task list"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('task:tasklist'))
        
        self.assertEqual(response.status_code, 403)

    def test_task_apply_view(self):
        """Test volunteer applying for a task"""
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.post(reverse('task:task_apply', args=[self.task.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirect after application
        self.assertTrue(TaskApplication.objects.filter(
            task=self.task, 
            volunteer=self.volunteer_user
        ).exists())

    def test_task_apply_duplicate_application(self):
        """Test that volunteers cannot apply twice for the same task"""
        # Create initial application
        TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='pending'
        )
        
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.post(reverse('task:task_apply', args=[self.task.id]))
        
        self.assertEqual(response.status_code, 302)
        # Should still have only one application
        self.assertEqual(TaskApplication.objects.filter(
            task=self.task, 
            volunteer=self.volunteer_user
        ).count(), 1)

    def test_approve_application_view(self):
        """Test client approving a volunteer application"""
        application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='pending'
        )
        
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('task:approve_application', args=[application.id]))
        
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.assertEqual(application.status, 'accepted')

    def test_reject_application_view(self):
        """Test client rejecting a volunteer application"""
        application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='pending'
        )
        
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('task:reject_application', args=[application.id]))
        
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.assertEqual(application.status, 'rejected')

    def test_cancel_task_view(self):
        """Test client cancelling a task"""
        # Create task that starts in more than 24 hours
        future_task = Task.objects.create(
            title='Future Task',
            description='Task to be cancelled',
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=2),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('task:cancel_task', args=[future_task.id]))
        
        self.assertEqual(response.status_code, 302)
        future_task.refresh_from_db()
        self.assertEqual(future_task.status, 'cancelled')

    def test_cancel_task_within_24h_forbidden(self):
        """Test that tasks cannot be cancelled within 24 hours"""
        # Create task that starts in less than 24 hours
        near_task = Task.objects.create(
            title='Near Task',
            description='Task starting soon',
            start_time=timezone.now() + timedelta(hours=12),
            end_time=timezone.now() + timedelta(hours=14),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('task:cancel_task', args=[near_task.id]))
        
        self.assertEqual(response.status_code, 302)
        near_task.refresh_from_db()
        self.assertNotEqual(near_task.status, 'cancelled')

    def test_myapplication_view(self):
        """Test volunteer viewing their applications"""
        TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='pending'
        )
        
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('task:myapplication'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Help with groceries')

    def test_task_ongoing_view_client(self):
        """Test client viewing ongoing tasks"""
        self.task.status = 'ongoing'
        self.task.save()
        
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('task:task_ongoing'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Help with groceries')

    def test_task_ongoing_view_volunteer(self):
        """Test volunteer viewing ongoing tasks"""
        self.task.status = 'ongoing'
        self.task.save()
        
        TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='accepted'
        )
        
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('task:task_ongoing'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Help with groceries')


class TaskFormTests(TestCase):
    """Test cases for Task forms"""
    
    def setUp(self):
        self.support_type = SupportType.objects.create(name='Shopping')

    def test_task_form_valid_data(self):
        """Test TaskForm with valid data"""
        form_data = {
            'title': 'Test Task',
            'description': 'Test description',
            'start_time': timezone.now() + timedelta(days=1),
            'end_time': timezone.now() + timedelta(days=1, hours=2),
            'vol_number': 1,
            'work_area': [self.support_type.id]
        }
        
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_form_invalid_vol_number(self):
        """Test TaskForm with invalid volunteer number"""
        form_data = {
            'title': 'Test Task',
            'description': 'Test description',
            'start_time': timezone.now() + timedelta(days=1),
            'end_time': timezone.now() + timedelta(days=1, hours=2),
            'vol_number': 0,  # Invalid: should be at least 1
            'work_area': [self.support_type.id]
        }
        
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('vol_number', form.errors)

    def test_task_form_missing_required_fields(self):
        """Test TaskForm with missing required fields"""
        form_data = {
            'description': 'Test description',
            # Missing title, start_time, end_time, vol_number, work_area
        }
        
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('start_time', form.errors)
        self.assertIn('end_time', form.errors)
        self.assertIn('vol_number', form.errors)

    def test_task_filter_form_valid_data(self):
        """Test TaskFilterForm with valid data"""
        form_data = {
            'keyword': 'shopping',
            'weekday': '0',  # Monday
            'time_block': 'morning',
            'work_area': self.support_type.id
        }
        
        form = TaskFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_filter_form_empty_data(self):
        """Test TaskFilterForm with empty data (all optional)"""
        form_data = {}
        
        form = TaskFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_feedback_form_valid_data(self):
        """Test FeedbackForm with valid data"""
        form_data = {
            'satisfied': 'True',
            'starred': True,
            'comment': 'Great work!',
            'to_user': 1
        }
        
        form = FeedbackForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_feedback_form_missing_required_fields(self):
        """Test FeedbackForm with missing required fields"""
        form_data = {
            'comment': 'Great work!',
            # Missing satisfied and to_user
        }
        
        form = FeedbackForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('satisfied', form.errors)
        self.assertIn('to_user', form.errors)

    def test_task_record_form_valid_data(self):
        """Test TaskRecordForm with valid data"""
        form_data = {
            'record_0': 'Completed shopping task successfully'
        }
        
        form = TaskRecordForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        record_list = form.get_record_list()
        self.assertEqual(len(record_list), 1)
        self.assertEqual(record_list[0], 'Completed shopping task successfully')

    def test_task_record_form_missing_required_field(self):
        """Test TaskRecordForm with missing required field"""
        form_data = {}
        
        form = TaskRecordForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('record_0', form.errors)


class TaskApplicationModelTests(TestCase):
    """Test cases for TaskApplication model methods"""
    
    def setUp(self):
        # Create test users
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
            first_name='Jane',
            last_name='Client',
            phone_number='1234567890',
            location='AB12 3CD'
        )
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='0987654321',
            location='AB12 3CD'
        )
        
        # Create task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        
        # Create application
        self.application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='pending'
        )

    def test_application_cancel_method(self):
        """Test application cancellation"""
        self.application.cancel()
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'cancelled')
        self.assertIsNotNone(self.application.cancelled_at)

    def test_application_complete_method(self):
        """Test application completion"""
        self.application.complete()
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'completed')
        self.assertIsNotNone(self.application.completed_at)

    def test_application_can_be_cancelled_within_24h(self):
        """Test application cannot be cancelled within 24 hours"""
        # Task starts in 12 hours
        self.task.start_time = timezone.now() + timedelta(hours=12)
        self.task.save()
        
        self.assertFalse(self.application.can_be_cancelled())

    def test_application_can_be_cancelled_beyond_24h(self):
        """Test application can be cancelled beyond 24 hours"""
        # Task starts in 2 days
        self.task.start_time = timezone.now() + timedelta(days=2)
        self.task.save()
        
        self.assertTrue(self.application.can_be_cancelled())

    def test_application_is_active_property(self):
        """Test application is_active property"""
        self.assertTrue(self.application.is_active)
        
        self.application.status = 'accepted'
        self.assertTrue(self.application.is_active)
        
        self.application.status = 'rejected'
        self.assertFalse(self.application.is_active)

    def test_application_is_closed_property(self):
        """Test application is_closed property"""
        self.assertFalse(self.application.is_closed)
        
        self.application.status = 'rejected'
        self.assertTrue(self.application.is_closed)
        
        self.application.status = 'completed'
        self.assertTrue(self.application.is_closed)

    def test_application_str_method(self):
        """Test application string representation"""
        expected = f"{self.volunteer_user.email} applies for {self.task.title}"
        self.assertEqual(str(self.application), expected)


class TaskStatusUpdateTests(TestCase):
    """Test cases for task status update methods"""
    
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
        
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            vol_number=2,
            client=self.client_user,
            status='open'
        )

    def test_update_status_by_time_before_start(self):
        """Test task status update before start time"""
        self.task.update_status_by_time()
        self.assertEqual(self.task.status, 'open')

    def test_update_status_by_time_during_task_with_volunteers(self):
        """Test task status update during task time with accepted volunteers"""
        # Set task to current time
        self.task.start_time = timezone.now() - timedelta(minutes=30)
        self.task.end_time = timezone.now() + timedelta(minutes=30)
        self.task.save()
        
        # Create accepted application
        TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='accepted'
        )
        
        self.task.update_status_by_time()
        self.assertEqual(self.task.status, 'ongoing')

    def test_update_status_by_time_during_task_no_volunteers(self):
        """Test task status update during task time without volunteers"""
        # Set task to current time
        self.task.start_time = timezone.now() - timedelta(minutes=30)
        self.task.end_time = timezone.now() + timedelta(minutes=30)
        self.task.save()
        
        self.task.update_status_by_time()
        self.assertEqual(self.task.status, 'cancelled')
        self.assertIsNotNone(self.task.closed_at)

    def test_update_status_by_time_after_end_confirmed(self):
        """Test task status update after end time with client confirmation"""
        # Set task to past
        self.task.start_time = timezone.now() - timedelta(hours=4)
        self.task.end_time = timezone.now() - timedelta(hours=1)
        self.task.confirmed_by_client = True
        self.task.save()
        
        # Create accepted application
        TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='accepted'
        )
        
        self.task.update_status_by_time()
        self.assertEqual(self.task.status, 'completed')

    def test_update_status_by_time_after_end_not_confirmed(self):
        """Test task status update after end time without client confirmation"""
        # Set task to past
        self.task.start_time = timezone.now() - timedelta(hours=4)
        self.task.end_time = timezone.now() - timedelta(hours=1)
        self.task.confirmed_by_client = False
        self.task.save()
        
        # Create accepted application
        TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='accepted'
        )
        
        self.task.update_status_by_time()
        self.assertEqual(self.task.status, 'timeout')


class TaskTemplateModelTests(TestCase):
    """Test cases for TaskTemplate model"""
    
    def setUp(self):
        self.support_type = SupportType.objects.create(name='Shopping')
        
        self.template = TaskTemplate.objects.create(
            name='Weekly Shopping Template',
            title='Weekly Shopping',
            description='Help with weekly grocery shopping'
        )
        self.template.work_area.add(self.support_type)

    def test_task_template_creation(self):
        """Test task template creation"""
        self.assertEqual(self.template.name, 'Weekly Shopping Template')
        self.assertEqual(self.template.title, 'Weekly Shopping')
        self.assertTrue(self.template.work_area.filter(name='Shopping').exists())

    def test_task_template_str_method(self):
        """Test task template string representation"""
        expected = 'Weekly Shopping Template'
        self.assertEqual(str(self.template), expected)


class TaskRecordModelTests(TestCase):
    """Test cases for TaskRecord model"""
    
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
        
        # Create user profiles
        UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='0987654321',
            location='AB12 3CD'
        )
        
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            vol_number=1,
            client=self.client_user,
            status='completed'
        )
        
        self.record = TaskRecord.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            records=['Task completed successfully', 'All items purchased']
        )

    def test_task_record_creation(self):
        """Test task record creation"""
        self.assertEqual(self.record.task, self.task)
        self.assertEqual(self.record.volunteer, self.volunteer_user)
        self.assertEqual(len(self.record.records), 2)
        self.assertIn('Task completed successfully', self.record.records)

    def test_task_record_str_method(self):
        """Test task record string representation"""
        expected = f"Record for {self.task.title} by John Volunteer [{self.volunteer_user.email}]"
        self.assertEqual(str(self.record), expected)


class FeedbackModelTests(TestCase):
    """Test cases for Feedback model"""
    
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
        
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            vol_number=1,
            client=self.client_user,
            status='completed'
        )
        
        self.feedback = Feedback.objects.create(
            task=self.task,
            from_user=self.client_user,
            to_user=self.volunteer_user,
            is_satisfied=True,
            comment='Excellent work!'
        )

    def test_feedback_creation(self):
        """Test feedback creation"""
        self.assertEqual(self.feedback.task, self.task)
        self.assertEqual(self.feedback.from_user, self.client_user)
        self.assertEqual(self.feedback.to_user, self.volunteer_user)
        self.assertTrue(self.feedback.is_satisfied)
        self.assertEqual(self.feedback.comment, 'Excellent work!')

    def test_feedback_unique_constraint(self):
        """Test unique constraint for task-from_user-to_user combination"""
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError):
            Feedback.objects.create(
                task=self.task,
                from_user=self.client_user,
                to_user=self.volunteer_user,
                is_satisfied=False,
                comment='Duplicate feedback'
            )


class StarRelationModelTests(TestCase):
    """Test cases for StarRelation model"""
    
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
        
        self.star_relation = StarRelation.objects.create(
            from_user=self.client_user,
            to_user=self.volunteer_user
        )

    def test_star_relation_creation(self):
        """Test star relation creation"""
        self.assertEqual(self.star_relation.from_user, self.client_user)
        self.assertEqual(self.star_relation.to_user, self.volunteer_user)
        self.assertIsNotNone(self.star_relation.starred_at)

    def test_star_relation_unique_constraint(self):
        """Test unique constraint for from_user-to_user combination"""
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError):
            StarRelation.objects.create(
                from_user=self.client_user,
                to_user=self.volunteer_user
            )


class TaskIntegrationTests(TestCase):
    """Integration tests for task workflow"""
    
    def setUp(self):
        # Create test users
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
            first_name='Jane',
            last_name='Client',
            phone_number='1234567890',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='0987654321',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        
        # Create client and volunteer profiles
        ClientProfile.objects.create(
            user_profile=self.client_profile,
            preferred_contact_method='email'
        )
        VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )
        
        self.support_type = SupportType.objects.create(name='Shopping')
        self.client = Client()

    def test_complete_task_workflow(self):
        """Test complete task workflow from creation to completion"""
        # Step 1: Client creates task
        self.client.login(email='client@test.com', password='testpass123')
        
        task_data = {
            'title': 'Integration Test Task',
            'description': 'Complete workflow test',
            'start_time': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': (timezone.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'vol_number': 1,
            'work_area': [self.support_type.id]
        }
        
        response = self.client.post(reverse('task:task_create'), task_data)
        self.assertEqual(response.status_code, 302)
        
        task = Task.objects.get(title='Integration Test Task')
        self.assertEqual(task.status, 'open')
        
        # Step 2: Volunteer applies for task
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.post(reverse('task:task_apply', args=[task.id]))
        self.assertEqual(response.status_code, 302)
        
        application = TaskApplication.objects.get(task=task, volunteer=self.volunteer_user)
        self.assertEqual(application.status, 'pending')
        
        # Step 3: Client approves application
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('task:approve_application', args=[application.id]))
        self.assertEqual(response.status_code, 302)
        
        application.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(application.status, 'accepted')
        self.assertEqual(task.status, 'selected')
        
        # Step 4: Task becomes ongoing (simulate time passage)
        task.status = 'ongoing'
        task.save()
        
        # Step 5: Volunteer submits record
        self.client.login(email='volunteer@test.com', password='testpass123')
        record_data = {
            'record_0': 'Task completed successfully'
        }
        response = self.client.post(reverse('task:task_record', args=[task.id]), record_data)
        self.assertEqual(response.status_code, 302)
        
        task.refresh_from_db()
        self.assertTrue(task.volunteer_submitted)
        
        # Step 6: Client confirms completion
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('task:task_confirm', args=[task.id]))
        self.assertEqual(response.status_code, 302)
        
        task.refresh_from_db()
        self.assertTrue(task.confirmed_by_client)
        self.assertEqual(task.status, 'completed')

    def test_task_cancellation_workflow(self):
        """Test task cancellation workflow"""
        # Create task that can be cancelled (starts in more than 24 hours)
        task = Task.objects.create(
            title='Cancellation Test Task',
            description='Task to be cancelled',
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=2),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        
        # Volunteer applies
        application = TaskApplication.objects.create(
            task=task,
            volunteer=self.volunteer_user,
            status='pending'
        )
        
        # Client cancels task
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.post(reverse('task:cancel_task', args=[task.id]))
        self.assertEqual(response.status_code, 302)
        
        task.refresh_from_db()
        application.refresh_from_db()
        
        self.assertEqual(task.status, 'cancelled')
        self.assertIsNotNone(task.closed_at)
        # Application should also be cancelled
        self.assertEqual(application.status, 'cancelled')