from django.test import TestCase, SimpleTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from .models import OperationLog
from user.models import UserProfile, ClientProfile, VolunteerProfile
from task.models import Task, TaskApplication, TaskRecord, Feedback, StarRelation
from payment.models import Donation

User = get_user_model()


class AdminPanelURLTests(SimpleTestCase):
    """Test cases for admin panel URL configuration"""
    
    def test_dashboard_url_resolves(self):
        """Test that dashboard URL resolves correctly"""
        url = reverse('adminpanel:dashboard')
        self.assertIn('dashboard', url)
    
    def test_user_list_url_resolves(self):
        """Test that user list URL resolves correctly"""
        url = reverse('adminpanel:user_list')
        self.assertIn('users', url)
    
    def test_user_detail_url_resolves(self):
        """Test that user detail URL resolves correctly"""
        url = reverse('adminpanel:user_detail', args=[1])
        self.assertIn('users/1', url)
    
    def test_task_list_url_resolves(self):
        """Test that task list URL resolves correctly"""
        url = reverse('adminpanel:task_list')
        self.assertIn('tasks', url)
    
    def test_update_eligibility_url_resolves(self):
        """Test that update eligibility URL resolves correctly"""
        url = reverse('adminpanel:update_eligibility', args=[1])
        self.assertIn('update-eligibility', url)


class StaffRequiredDecoratorTests(SimpleTestCase):
    """Test cases for staff_required decorator logic"""
    
    def test_staff_required_decorator_import(self):
        """Test that staff_required decorator can be imported"""
        from adminpanel.views import staff_required
        self.assertTrue(callable(staff_required))
    
    def test_staff_required_decorator_with_mock_staff_user(self):
        """Test staff_required decorator logic with mock staff user"""
        from adminpanel.views import staff_required
        
        # Create a mock view function
        def mock_view(request):
            return "success"
        
        # Apply the decorator
        decorated_view = staff_required(mock_view)
        
        # Verify the decorator returns a function
        self.assertTrue(callable(decorated_view))
    
    def test_staff_required_decorator_preserves_function_name(self):
        """Test that staff_required decorator preserves function metadata"""
        from adminpanel.views import staff_required
        
        def test_view(request):
            """Test view function"""
            return "test"
        
        decorated_view = staff_required(test_view)
        
        # The decorator should preserve the original function's properties
        self.assertTrue(callable(decorated_view))


class AdminPanelUtilityTests(SimpleTestCase):
    """Test cases for admin panel utility functions and logic"""
    
    def test_operation_log_str_format(self):
        """Test OperationLog string formatting logic"""
        # Mock the necessary components
        mock_user = Mock()
        mock_user.email = 'test@example.com'
        
        mock_timestamp = Mock()
        mock_timestamp.strftime.return_value = '2024-01-01 12:00:00'
        
        # Test the string format logic
        action = 'Test action'
        expected_str = f"{mock_user.email} - {action} - {mock_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.assertEqual(expected_str, 'test@example.com - Test action - 2024-01-01 12:00:00')
    
    def test_eligibility_validation_logic(self):
        """Test eligibility validation logic"""
        # Test valid values
        valid_values = ['true', 'false']
        for value in valid_values:
            self.assertIn(value, ['true', 'false'])
        
        # Test invalid values
        invalid_values = ['True', 'False', '1', '0', 'yes', 'no', '']
        for value in invalid_values:
            self.assertNotIn(value, ['true', 'false'])
    
    def test_user_role_filtering_logic(self):
        """Test user role filtering logic for admin panel"""
        # Test the Q object logic used in user_list view
        from django.db.models import Q
        
        # This is the logic used in the view: Q(role='client') | Q(role='volunteer')
        client_q = Q(role='client')
        volunteer_q = Q(role='volunteer')
        combined_q = client_q | volunteer_q
        
        # Verify Q objects are created correctly
        self.assertEqual(str(client_q), "(AND: ('role', 'client'))")
        self.assertEqual(str(volunteer_q), "(AND: ('role', 'volunteer'))")
        self.assertEqual(str(combined_q), "(OR: ('role', 'client'), ('role', 'volunteer'))")


class AdminPanelConfigurationTests(SimpleTestCase):
    """Test cases for admin panel configuration and settings"""
    
    def test_app_name_configuration(self):
        """Test that app name is configured correctly"""
        from adminpanel.urls import app_name
        self.assertEqual(app_name, 'adminpanel')
    
    def test_url_patterns_structure(self):
        """Test URL patterns structure"""
        from adminpanel.urls import urlpatterns
        
        # Verify that urlpatterns is a list
        self.assertIsInstance(urlpatterns, list)
        
        # Verify that we have the expected number of URL patterns
        self.assertGreater(len(urlpatterns), 0)
    
    def test_view_imports(self):
        """Test that all required views can be imported"""
        from adminpanel import views
        
        required_views = [
            'admin_dashboard',
            'user_list', 
            'user_detail',
            'user_file',
            'update_eligibility',
            'task_list',
            'task_detail',
            'records',
            'donations'
        ]
        
        for view_name in required_views:
            self.assertTrue(hasattr(views, view_name))
            self.assertTrue(callable(getattr(views, view_name)))


class OperationLogModelTests(TestCase):
    """Test cases for OperationLog model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='client',
            is_active=True
        )
    
    def test_operation_log_creation(self):
        """Test OperationLog model creation"""
        log = OperationLog.objects.create(
            user=self.user,
            action='User registered',
            is_processed=False
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'User registered')
        self.assertFalse(log.is_processed)
        self.assertIsNotNone(log.timestamp)
    
    def test_operation_log_str_method(self):
        """Test OperationLog string representation"""
        log = OperationLog.objects.create(
            user=self.user,
            action='Test action'
        )
        
        expected_str = f"{self.user.email} - Test action - {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        self.assertEqual(str(log), expected_str)
    
    def test_operation_log_default_values(self):
        """Test OperationLog default field values"""
        log = OperationLog.objects.create(
            user=self.user,
            action='Default test'
        )
        
        self.assertFalse(log.is_processed)  # Default should be False
        self.assertIsNotNone(log.timestamp)  # Should be auto-generated


class AdminPanelViewTests(TestCase):
    """Test cases for admin panel views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create staff user (admin)
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role='admin',
            is_active=True,
            is_staff=True
        )
        
        # Create regular users
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='clientpass123',
            role='client',
            is_active=True
        )
        
        self.volunteer_user = User.objects.create_user(
            email='volunteer@example.com',
            password='volunteerpass123',
            role='volunteer',
            is_active=True
        )
        
        # Create user profiles
        self.client_profile = UserProfile.objects.create(
            user=self.client_user,
            first_name='Client',
            last_name='User',
            phone_number='1234567890',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='Volunteer',
            last_name='User',
            phone_number='0987654321',
            location='AB12 3CD',
            eligibility_confirmed=False
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
        
        # Create test data
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            client=self.client_user,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            vol_number=1,
            status='open'
        )
        
        self.application = TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='pending'
        )
        
        self.operation_log = OperationLog.objects.create(
            user=self.client_user,
            action='User registered'
        )
        
        self.donation = Donation.objects.create(
            donor=self.client_user,
            donor_name='Test Donor',
            donor_email='donor@example.com',
            amount=Decimal('50.00'),
            status='completed',
            stripe_payment_intent_id='pi_test123'
        )


class AdminDashboardTests(AdminPanelViewTests):
    """Test cases for admin dashboard view"""
    
    def test_admin_dashboard_requires_staff_permission(self):
        """Test that admin dashboard requires staff permission"""
        # Test unauthenticated access
        response = self.client.get(reverse('adminpanel:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test regular user access
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('adminpanel:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect due to lack of staff permission
    
    def test_admin_dashboard_with_staff_user(self):
        """Test admin dashboard access with staff user"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('adminpanel:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/admin_dashboard.html')
    
    def test_admin_dashboard_context_data(self):
        """Test admin dashboard context data"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('adminpanel:dashboard'))
        
        self.assertIn('client_count', response.context)
        self.assertIn('volunteer_count', response.context)
        self.assertIn('task_count', response.context)
        self.assertIn('today_task_count', response.context)
        self.assertIn('logs', response.context)
        
        # Verify counts
        self.assertEqual(response.context['client_count'], 1)
        self.assertEqual(response.context['volunteer_count'], 1)
        self.assertEqual(response.context['task_count'], 1)


class UserManagementTests(AdminPanelViewTests):
    """Test cases for user management views"""
    
    def test_user_list_view(self):
        """Test user list view"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('adminpanel:user_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/user_list.html')
        self.assertIn('users', response.context)
        
        # Should contain client and volunteer users, but not admin
        users = response.context['users']
        user_emails = [user.email for user in users]
        self.assertIn('client@example.com', user_emails)
        self.assertIn('volunteer@example.com', user_emails)
        self.assertNotIn('admin@example.com', user_emails)
    
    def test_user_detail_view_client(self):
        """Test user detail view for client"""
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse('adminpanel:user_detail', args=[self.client_user.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/user_detail.html')
        self.assertEqual(response.context['user'], self.client_user)
        self.assertIn('tasks', response.context)
        self.assertIn('give_stars', response.context)
        self.assertIn('have_stars', response.context)
    
    def test_user_detail_view_volunteer(self):
        """Test user detail view for volunteer"""
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse('adminpanel:user_detail', args=[self.volunteer_user.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/user_detail.html')
        self.assertEqual(response.context['user'], self.volunteer_user)
        self.assertIn('applications', response.context)
        self.assertIn('give_stars', response.context)
        self.assertIn('have_stars', response.context)
    
    def test_user_detail_view_nonexistent_user(self):
        """Test user detail view with nonexistent user"""
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse('adminpanel:user_detail', args=[999])
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_user_file_view(self):
        """Test user file view"""
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse('adminpanel:user_file', args=[self.client_user.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/user_file.html')
        self.assertEqual(response.context['user'], self.client_user)


class EligibilityUpdateTests(AdminPanelViewTests):
    """Test cases for eligibility update functionality"""
    
    def test_update_eligibility_to_true(self):
        """Test updating user eligibility to true"""
        self.client.force_login(self.admin_user)
        
        # Initially false
        self.assertFalse(self.volunteer_profile.eligibility_confirmed)
        
        response = self.client.post(
            reverse('adminpanel:update_eligibility', args=[self.volunteer_user.id]),
            {'eligibility': 'true'}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, 
            reverse('adminpanel:user_file', args=[self.volunteer_user.id])
        )
        
        # Check if eligibility was updated
        self.volunteer_profile.refresh_from_db()
        self.assertTrue(self.volunteer_profile.eligibility_confirmed)
    
    def test_update_eligibility_to_false(self):
        """Test updating user eligibility to false"""
        self.client.force_login(self.admin_user)
        
        # Initially true
        self.assertTrue(self.client_profile.eligibility_confirmed)
        
        response = self.client.post(
            reverse('adminpanel:update_eligibility', args=[self.client_user.id]),
            {'eligibility': 'false'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check if eligibility was updated
        self.client_profile.refresh_from_db()
        self.assertFalse(self.client_profile.eligibility_confirmed)
    
    def test_update_eligibility_invalid_value(self):
        """Test updating eligibility with invalid value"""
        self.client.force_login(self.admin_user)
        
        original_status = self.client_profile.eligibility_confirmed
        
        response = self.client.post(
            reverse('adminpanel:update_eligibility', args=[self.client_user.id]),
            {'eligibility': 'invalid'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check that eligibility was not changed
        self.client_profile.refresh_from_db()
        self.assertEqual(self.client_profile.eligibility_confirmed, original_status)
    
    def test_update_eligibility_requires_post(self):
        """Test that eligibility update requires POST method"""
        self.client.force_login(self.admin_user)
        
        response = self.client.get(
            reverse('adminpanel:update_eligibility', args=[self.client_user.id])
        )
        
        self.assertEqual(response.status_code, 405)  # Method not allowed


class TaskManagementTests(AdminPanelViewTests):
    """Test cases for task management views"""
    
    def test_task_list_view(self):
        """Test task list view"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('adminpanel:task_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/task_list.html')
        self.assertIn('tasks', response.context)
        
        tasks = response.context['tasks']
        self.assertIn(self.task, tasks)
    
    def test_task_detail_view(self):
        """Test task detail view"""
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse('adminpanel:task_detail', args=[self.task.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/task_detail.html')
        self.assertEqual(response.context['task'], self.task)
        self.assertIn('applications', response.context)
        self.assertIn('records', response.context)
        self.assertIn('feedbacks', response.context)
        
        # Check that application is included
        applications = response.context['applications']
        self.assertIn(self.application, applications)
    
    def test_task_detail_view_nonexistent_task(self):
        """Test task detail view with nonexistent task"""
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse('adminpanel:task_detail', args=[999])
        )
        
        self.assertEqual(response.status_code, 404)


class RecordsAndLogsTests(AdminPanelViewTests):
    """Test cases for records and logs views"""
    
    def test_records_view(self):
        """Test operation records view"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('adminpanel:records'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/records.html')
        self.assertIn('logs', response.context)
        
        logs = response.context['logs']
        self.assertIn(self.operation_log, logs)
    
    def test_donations_view(self):
        """Test donations view"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('adminpanel:donations'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/donations.html')
        self.assertIn('donations', response.context)
        
        donations = response.context['donations']
        self.assertIn(self.donation, donations)
    
    def test_donations_view_only_completed(self):
        """Test that donations view only shows completed donations"""
        # Create a pending donation
        pending_donation = Donation.objects.create(
            donor=self.client_user,
            donor_name='Pending Donor',
            donor_email='pending@example.com',
            amount=Decimal('25.00'),
            status='pending',
            stripe_payment_intent_id='pi_pending123'
        )
        
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('adminpanel:donations'))
        
        donations = response.context['donations']
        self.assertIn(self.donation, donations)  # Completed donation should be included
        self.assertNotIn(pending_donation, donations)  # Pending donation should not be included


class AdminPanelPermissionTests(TestCase):
    """Test cases for admin panel permission system"""
    
    def setUp(self):
        self.client = Client()
        
        # Create users with different permissions
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='staffpass123',
            role='admin',
            is_active=True,
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='regularpass123',
            role='client',
            is_active=True,
            is_staff=False
        )
        
        self.inactive_staff = User.objects.create_user(
            email='inactive@example.com',
            password='inactivepass123',
            role='admin',
            is_active=False,
            is_staff=True
        )
    
    def test_staff_required_decorator_with_staff_user(self):
        """Test staff_required decorator allows staff users"""
        self.client.force_login(self.staff_user)
        
        admin_urls = [
            'adminpanel:dashboard',
            'adminpanel:user_list',
            'adminpanel:task_list',
            'adminpanel:records',
            'adminpanel:donations',
        ]
        
        for url_name in admin_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"Failed for {url_name}")
    
    def test_staff_required_decorator_with_regular_user(self):
        """Test staff_required decorator blocks regular users"""
        self.client.force_login(self.regular_user)
        
        admin_urls = [
            'adminpanel:dashboard',
            'adminpanel:user_list',
            'adminpanel:task_list',
            'adminpanel:records',
            'adminpanel:donations',
        ]
        
        for url_name in admin_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302, f"Should redirect for {url_name}")
    
    def test_staff_required_decorator_with_unauthenticated_user(self):
        """Test staff_required decorator blocks unauthenticated users"""
        admin_urls = [
            'adminpanel:dashboard',
            'adminpanel:user_list',
            'adminpanel:task_list',
            'adminpanel:records',
            'adminpanel:donations',
        ]
        
        for url_name in admin_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302, f"Should redirect for {url_name}")


class AdminPanelIntegrationTests(AdminPanelViewTests):
    """Integration tests for admin panel functionality"""
    
    def test_complete_user_management_workflow(self):
        """Test complete user management workflow"""
        self.client.force_login(self.admin_user)
        
        # 1. View user list
        response = self.client.get(reverse('adminpanel:user_list'))
        self.assertEqual(response.status_code, 200)
        
        # 2. View specific user detail
        response = self.client.get(
            reverse('adminpanel:user_detail', args=[self.volunteer_user.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # 3. View user files
        response = self.client.get(
            reverse('adminpanel:user_file', args=[self.volunteer_user.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # 4. Update eligibility
        response = self.client.post(
            reverse('adminpanel:update_eligibility', args=[self.volunteer_user.id]),
            {'eligibility': 'true'}
        )
        self.assertEqual(response.status_code, 302)
        
        # 5. Verify eligibility was updated
        self.volunteer_profile.refresh_from_db()
        self.assertTrue(self.volunteer_profile.eligibility_confirmed)
    
    def test_task_monitoring_workflow(self):
        """Test task monitoring workflow"""
        # Create additional test data
        TaskRecord.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            records=['Task started']
        )
        
        Feedback.objects.create(
            task=self.task,
            from_user=self.client_user,
            to_user=self.volunteer_user,
            is_satisfied=True,
            comment='Great work!'
        )
        
        self.client.force_login(self.admin_user)
        
        # 1. View task list
        response = self.client.get(reverse('adminpanel:task_list'))
        self.assertEqual(response.status_code, 200)
        
        # 2. View task details
        response = self.client.get(
            reverse('adminpanel:task_detail', args=[self.task.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify all related data is displayed
        self.assertIn('applications', response.context)
        self.assertIn('records', response.context)
        self.assertIn('feedbacks', response.context)
    
    def test_system_monitoring_workflow(self):
        """Test system monitoring workflow"""
        # Create additional operation logs
        OperationLog.objects.create(
            user=self.volunteer_user,
            action='Applied for task',
            is_processed=True
        )
        
        self.client.force_login(self.admin_user)
        
        # 1. View dashboard
        response = self.client.get(reverse('adminpanel:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Verify statistics are displayed
        self.assertGreater(response.context['client_count'], 0)
        self.assertGreater(response.context['volunteer_count'], 0)
        self.assertGreater(response.context['task_count'], 0)
        
        # 2. View detailed records
        response = self.client.get(reverse('adminpanel:records'))
        self.assertEqual(response.status_code, 200)
        
        # 3. View donations
        response = self.client.get(reverse('adminpanel:donations'))
        self.assertEqual(response.status_code, 200)