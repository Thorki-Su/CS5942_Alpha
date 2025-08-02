from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
from io import BytesIO

from user.models import UserProfile, VolunteerProfile
from task.models import Task, TaskApplication
from .utils import calculate_volunteer_duration, format_volunteer_duration
from .views import service_certificate, download_certificate, get_volunteer_stats

User = get_user_model()


class VolunteerUtilsTests(TestCase):
    """Test cases for volunteer utility functions"""
    
    def setUp(self):
        # Create test users
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        
        # Create user profiles
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='1234567890',
            location='AB12 3CD'
        )
        self.client_profile = UserProfile.objects.create(
            user=self.client_user,
            first_name='Jane',
            last_name='Client',
            phone_number='0987654321',
            location='AB12 3CD'
        )
        
        # Create volunteer profile
        VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )
        
        # Create test tasks with different durations
        self.task1 = Task.objects.create(
            client=self.client_user,
            title='Task 1',
            description='Test task 1',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),  # 2 hours
            vol_number=1,
            status='completed'
        )
        
        self.task2 = Task.objects.create(
            client=self.client_user,
            title='Task 2',
            description='Test task 2',
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=3, minutes=30),  # 3.5 hours
            vol_number=1,
            status='completed'
        )
        
        self.task3 = Task.objects.create(
            client=self.client_user,
            title='Task 3',
            description='Test task 3',
            start_time=timezone.now() + timedelta(days=3),
            end_time=timezone.now() + timedelta(days=3, hours=1),  # 1 hour
            vol_number=1,
            status='ongoing'
        )

    def test_calculate_volunteer_duration_no_tasks(self):
        """Test volunteer duration calculation with no completed tasks"""
        duration = calculate_volunteer_duration(self.volunteer_user)
        self.assertAlmostEqual(duration, 0.0, places=1)

    def test_calculate_volunteer_duration_with_completed_tasks(self):
        """Test volunteer duration calculation with completed tasks"""
        # Create completed task applications
        TaskApplication.objects.create(
            task=self.task1,
            volunteer=self.volunteer_user,
            status='completed'
        )
        TaskApplication.objects.create(
            task=self.task2,
            volunteer=self.volunteer_user,
            status='completed'
        )
        
        duration = calculate_volunteer_duration(self.volunteer_user)
        expected_duration = 2.0 + 3.5  # 5.5 hours total
        self.assertAlmostEqual(duration, expected_duration, places=1)

    def test_calculate_volunteer_duration_excludes_non_completed(self):
        """Test that non-completed tasks are excluded from duration calculation"""
        # Create applications with different statuses
        TaskApplication.objects.create(
            task=self.task1,
            volunteer=self.volunteer_user,
            status='completed'
        )
        TaskApplication.objects.create(
            task=self.task2,
            volunteer=self.volunteer_user,
            status='pending'
        )
        TaskApplication.objects.create(
            task=self.task3,
            volunteer=self.volunteer_user,
            status='rejected'
        )
        
        duration = calculate_volunteer_duration(self.volunteer_user)
        expected_duration = 2.0  # Only completed task
        self.assertAlmostEqual(duration, expected_duration, places=1)

    def test_format_volunteer_duration_zero_hours(self):
        """Test formatting zero hours"""
        formatted = format_volunteer_duration(0)
        self.assertEqual(formatted, "0 hours")

    def test_format_volunteer_duration_less_than_hour(self):
        """Test formatting duration less than an hour"""
        formatted = format_volunteer_duration(0.5)  # 30 minutes
        self.assertEqual(formatted, "30 minutes")

    def test_format_volunteer_duration_exact_hours(self):
        """Test formatting exact hours"""
        formatted = format_volunteer_duration(2.0)
        self.assertEqual(formatted, "2 hours")
        
        formatted = format_volunteer_duration(1.0)
        self.assertEqual(formatted, "1 hour")

    def test_format_volunteer_duration_hours_and_minutes(self):
        """Test formatting hours and minutes"""
        formatted = format_volunteer_duration(2.5)  # 2 hours 30 minutes
        self.assertEqual(formatted, "2 hours 30 minutes")

    def test_format_volunteer_duration_days(self):
        """Test formatting days and hours"""
        formatted = format_volunteer_duration(25.0)  # 1 day 1 hour
        self.assertEqual(formatted, "1 day 1 hour")
        
        formatted = format_volunteer_duration(48.0)  # 2 days
        self.assertEqual(formatted, "2 days")

    def test_format_volunteer_duration_days_no_minutes(self):
        """Test that minutes are not shown when duration includes days"""
        formatted = format_volunteer_duration(24.5)  # 1 day 30 minutes
        self.assertEqual(formatted, "1 day")


class VolunteerViewsTests(TestCase):
    """Test cases for volunteer views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_active=True
        )
        
        # Create user profiles
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='1234567890',
            location='AB12 3CD'
        )
        self.client_profile = UserProfile.objects.create(
            user=self.client_user,
            first_name='Jane',
            last_name='Client',
            phone_number='0987654321',
            location='AB12 3CD'
        )
        
        # Create volunteer profile
        VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )

    def test_service_certificate_view_unauthenticated(self):
        """Test service certificate view requires authentication"""
        response = self.client.get(reverse('volunteer:service_certificate'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    # def test_service_certificate_view_non_volunteer(self):
    #     """Test service certificate view denies access to non-volunteers"""
    #     self.client.force_login(self.client_user)
    #     response = self.client.get(reverse('volunteer:service_certificate'))
    #     self.assertRedirects(response, reverse('user:profile_detail'))

    def test_service_certificate_view_no_hours(self):
        """Test service certificate view with no volunteer hours"""
        self.client.force_login(self.volunteer_user)
        response = self.client.get(reverse('volunteer:service_certificate'))
        self.assertRedirects(response, reverse('user:profile_detail'))

    @patch('volunteer.views.calculate_volunteer_duration')
    def test_service_certificate_view_with_hours(self, mock_calculate):
        """Test service certificate view with volunteer hours"""
        mock_calculate.return_value = 10.5
        
        self.client.force_login(self.volunteer_user)
        response = self.client.get(reverse('volunteer:service_certificate'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'volunteer/service_certificate.html')
        self.assertIn('total_hours', response.context)
        self.assertIn('formatted_duration', response.context)
        self.assertAlmostEqual(response.context['total_hours'], 10.5, places=1)

    def test_download_certificate_unauthenticated(self):
        """Test download certificate requires authentication"""
        response = self.client.get(reverse('volunteer:download_certificate'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_download_certificate_non_volunteer(self):
        """Test download certificate denies access to non-volunteers"""
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('volunteer:download_certificate'))
        self.assertEqual(response.status_code, 403)
        
        data = response.json()
        self.assertEqual(data['error'], 'Access denied')

    @patch('volunteer.views.calculate_volunteer_duration')
    def test_download_certificate_no_hours(self, mock_calculate):
        """Test download certificate with no volunteer hours"""
        mock_calculate.return_value = 0
        
        self.client.force_login(self.volunteer_user)
        response = self.client.get(reverse('volunteer:download_certificate'))
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertEqual(data['error'], 'No volunteer hours recorded')

    @patch('volunteer.views.calculate_volunteer_duration')
    @patch('volunteer.views.format_volunteer_duration')
    def test_download_certificate_success(self, mock_format, mock_calculate):
        """Test successful certificate download"""
        mock_calculate.return_value = 15.5
        mock_format.return_value = "15 hours 30 minutes"
        
        self.client.force_login(self.volunteer_user)
        response = self.client.get(reverse('volunteer:download_certificate'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('volunteer_certificate_John_Volunteer.pdf', response['Content-Disposition'])

    def test_get_volunteer_stats_unauthenticated(self):
        """Test volunteer stats API requires authentication"""
        response = self.client.get(reverse('volunteer:get_volunteer_stats'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_volunteer_stats_non_volunteer(self):
        """Test volunteer stats API denies access to non-volunteers"""
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('volunteer:get_volunteer_stats'))
        self.assertEqual(response.status_code, 403)
        
        data = response.json()
        self.assertEqual(data['error'], 'Access denied')

    @patch('volunteer.views.calculate_volunteer_duration')
    @patch('volunteer.views.format_volunteer_duration')
    def test_get_volunteer_stats_success(self, mock_format, mock_calculate):
        """Test successful volunteer stats API call"""
        mock_calculate.return_value = 8.25
        mock_format.return_value = "8 hours 15 minutes"
        
        self.client.force_login(self.volunteer_user)
        response = self.client.get(reverse('volunteer:get_volunteer_stats'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertAlmostEqual(data['total_hours'], 8.25, places=1)
        self.assertEqual(data['formatted_duration'], "8 hours 15 minutes")


class VolunteerIntegrationTests(TestCase):
    """Integration tests for volunteer functionality"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        
        # Create user profiles
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='1234567890',
            location='AB12 3CD'
        )
        self.client_profile = UserProfile.objects.create(
            user=self.client_user,
            first_name='Jane',
            last_name='Client',
            phone_number='0987654321',
            location='AB12 3CD'
        )
        
        # Create volunteer profile
        VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )

    def test_complete_volunteer_certificate_workflow(self):
        """Test complete workflow from task completion to certificate generation"""
        # 1. Create a task
        task = Task.objects.create(
            client=self.client_user,
            title='Help with groceries',
            description='Need help with weekly shopping',
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=3),  # 2 hours
            vol_number=1,
            status='open'
        )
        
        # 2. Volunteer applies for task
        application = TaskApplication.objects.create(
            task=task,
            volunteer=self.volunteer_user,
            status='accepted'
        )
        
        # 3. Task is completed
        task.status = 'completed'
        task.save()
        application.status = 'completed'
        application.save()
        
        # 4. Check volunteer duration calculation
        duration = calculate_volunteer_duration(self.volunteer_user)
        self.assertAlmostEqual(duration, 2.0, places=1)  # 2 hours
        
        # 5. Check duration formatting
        formatted = format_volunteer_duration(duration)
        self.assertEqual(formatted, "2 hours")
        
        # 6. Access certificate page
        self.client.force_login(self.volunteer_user)
        response = self.client.get(reverse('volunteer:service_certificate'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Volunteer')
        self.assertContains(response, '2 hours')
        
        # 7. Download certificate
        response = self.client.get(reverse('volunteer:download_certificate'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
        # 8. Get stats via API
        response = self.client.get(reverse('volunteer:get_volunteer_stats'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertAlmostEqual(data['total_hours'], 2.0, places=1)
        self.assertEqual(data['formatted_duration'], "2 hours")

    def test_multiple_tasks_duration_accumulation(self):
        """Test that volunteer hours accumulate across multiple completed tasks"""
        # Create multiple tasks with different durations
        tasks_data = [
            {'hours': 1.5, 'title': 'Task 1'},
            {'hours': 2.0, 'title': 'Task 2'},
            {'hours': 0.5, 'title': 'Task 3'},
            {'hours': 3.0, 'title': 'Task 4'},
        ]
        
        total_expected_hours = 0
        
        for task_data in tasks_data:
            # Create task
            task = Task.objects.create(
                client=self.client_user,
                title=task_data['title'],
                description=f"Test {task_data['title']}",
                start_time=timezone.now() + timedelta(days=1),
                end_time=timezone.now() + timedelta(days=1, hours=task_data['hours']),
                vol_number=1,
                status='completed'
            )
            
            # Create completed application
            TaskApplication.objects.create(
                task=task,
                volunteer=self.volunteer_user,
                status='completed'
            )
            
            total_expected_hours += task_data['hours']
        
        # Check total duration
        duration = calculate_volunteer_duration(self.volunteer_user)
        self.assertAlmostEqual(duration, total_expected_hours, places=1)  # 7.0 hours total
        
        # Check formatting
        formatted = format_volunteer_duration(duration)
        self.assertEqual(formatted, "7 hours")

    def test_volunteer_certificate_content_accuracy(self):
        """Test that certificate contains accurate volunteer information"""
        # Create a completed task
        task = Task.objects.create(
            client=self.client_user,
            title='Community Support',
            description='Help elderly with daily tasks',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=4, minutes=30),  # 4.5 hours
            vol_number=1,
            status='completed'
        )
        
        TaskApplication.objects.create(
            task=task,
            volunteer=self.volunteer_user,
            status='completed'
        )
        
        # Access certificate page
        self.client.force_login(self.volunteer_user)
        response = self.client.get(reverse('volunteer:service_certificate'))
        
        # Verify context data
        self.assertAlmostEqual(response.context['total_hours'], 4.5, places=1)
        self.assertEqual(response.context['formatted_duration'], "4 hours 30 minutes")
        self.assertEqual(response.context['user_profile'].get_full_name, "John Volunteer")
        self.assertIn('current_date', response.context)

    def test_volunteer_stats_api_consistency(self):
        """Test that volunteer stats API returns consistent data with views"""
        # Create completed tasks
        for i in range(3):
            task = Task.objects.create(
                client=self.client_user,
                title=f'Task {i+1}',
                description=f'Test task {i+1}',
                start_time=timezone.now() + timedelta(days=i+1),
                end_time=timezone.now() + timedelta(days=i+1, hours=2),  # 2 hours each
                vol_number=1,
                status='completed'
            )
            
            TaskApplication.objects.create(
                task=task,
                volunteer=self.volunteer_user,
                status='completed'
            )
        
        # Get stats via API
        self.client.force_login(self.volunteer_user)
        api_response = self.client.get(reverse('volunteer:get_volunteer_stats'))
        api_data = api_response.json()
        
        # Get stats via certificate view
        cert_response = self.client.get(reverse('volunteer:service_certificate'))
        
        # Verify consistency
        self.assertEqual(api_data['total_hours'], cert_response.context['total_hours'])
        self.assertEqual(api_data['formatted_duration'], cert_response.context['formatted_duration'])
        self.assertAlmostEqual(api_data['total_hours'], 6.0, places=1)  # 3 tasks × 2 hours each


class VolunteerEdgeCaseTests(TestCase):
    """Test edge cases and error conditions for volunteer functionality"""
    
    def setUp(self):
        self.client = Client()
        
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='Test',
            last_name='Volunteer',
            phone_number='1234567890',
            location='AB12 3CD'
        )
        
        VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Test Course',
            profession='Student'
        )

    def test_volunteer_with_no_profile(self):
        """Test volunteer functionality when user profile is missing"""
        # Create user without profile
        user_no_profile = User.objects.create_user(
            email='noprofile@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        # Should handle gracefully
        duration = calculate_volunteer_duration(user_no_profile)
        self.assertAlmostEqual(duration, 0.0, places=1)

    def test_task_with_zero_duration(self):
        """Test handling of tasks with zero or negative duration"""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        
        # Create task with same start and end time
        task = Task.objects.create(
            client=client_user,
            title='Zero Duration Task',
            description='Task with no duration',
            start_time=timezone.now(),
            end_time=timezone.now(),  # Same time
            vol_number=1,
            status='completed'
        )
        
        TaskApplication.objects.create(
            task=task,
            volunteer=self.volunteer_user,
            status='completed'
        )
        
        duration = calculate_volunteer_duration(self.volunteer_user)
        self.assertAlmostEqual(duration, 0.0, places=1)

    def test_format_duration_edge_cases(self):
        """Test duration formatting edge cases"""
        # Test very small duration
        formatted = format_volunteer_duration(0.01)  # 0.6 minutes
        self.assertEqual(formatted, "0 hours")  # Should round down
        
        # Test exactly 1 minute
        formatted = format_volunteer_duration(1/60)  # 1 minute
        self.assertEqual(formatted, "1 minute")
        
        # Test exactly 1 hour
        formatted = format_volunteer_duration(1.0)
        self.assertEqual(formatted, "1 hour")
        
        # Test exactly 1 day
        formatted = format_volunteer_duration(24.0)
        self.assertEqual(formatted, "1 day")

    @patch('volunteer.views.calculate_volunteer_duration')
    def test_certificate_download_with_special_characters_in_name(self, mock_calculate):
        """Test certificate download with special characters in volunteer name"""
        mock_calculate.return_value = 5.0
        
        # Update profile with special characters
        self.volunteer_profile.first_name = "José"
        self.volunteer_profile.last_name = "García-Smith"
        self.volunteer_profile.save()
        
        self.client.force_login(self.volunteer_user)
        response = self.client.get(reverse('volunteer:download_certificate'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        # Filename should handle special characters
        self.assertIn('volunteer_certificate_José_García-Smith.pdf', response['Content-Disposition'])

    def test_concurrent_task_applications(self):
        """Test volunteer duration calculation with overlapping tasks"""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        
        base_time = timezone.now()
        
        # Create overlapping tasks
        task1 = Task.objects.create(
            client=client_user,
            title='Overlapping Task 1',
            description='First overlapping task',
            start_time=base_time,
            end_time=base_time + timedelta(hours=3),
            vol_number=1,
            status='completed'
        )
        
        task2 = Task.objects.create(
            client=client_user,
            title='Overlapping Task 2',
            description='Second overlapping task',
            start_time=base_time + timedelta(hours=1),  # Overlaps with task1
            end_time=base_time + timedelta(hours=4),
            vol_number=1,
            status='completed'
        )
        
        # Create applications for both tasks
        TaskApplication.objects.create(
            task=task1,
            volunteer=self.volunteer_user,
            status='completed'
        )
        TaskApplication.objects.create(
            task=task2,
            volunteer=self.volunteer_user,
            status='completed'
        )
        
        # Duration should be sum of both tasks (even if overlapping)
        duration = calculate_volunteer_duration(self.volunteer_user)
        self.assertAlmostEqual(duration, 6.0, places=1)  # 3 + 3 hours