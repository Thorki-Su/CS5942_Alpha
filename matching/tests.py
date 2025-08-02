from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time
from unittest.mock import patch, Mock

from user.models import UserProfile, ClientProfile, VolunteerProfile, SupportType
from task.models import Task, TaskApplication, StarRelation
from .forms import VolunteerAvailabilityForm
from .utils import haversine_distance, get_star_score, match_volunteers_for_task

User = get_user_model()


class MatchingUtilsTests(TestCase):
    """Test cases for matching utility functions"""
    
    def test_haversine_distance_calculation(self):
        """Test haversine distance calculation between two points"""
        # Test distance between London and Paris (approximately 344 km)
        london_lat, london_lon = 51.5074, -0.1278
        paris_lat, paris_lon = 48.8566, 2.3522
        
        distance = haversine_distance(london_lat, london_lon, paris_lat, paris_lon)
        
        # Allow some tolerance for floating point calculations
        self.assertAlmostEqual(distance, 344, delta=10)

    def test_haversine_distance_same_location(self):
        """Test haversine distance for same location should be 0"""
        lat, lon = 51.5074, -0.1278
        
        distance = haversine_distance(lat, lon, lat, lon)
        
        self.assertAlmostEqual(distance, 0, delta=0.1)

    def test_get_star_score_no_stars(self):
        """Test star score calculation with no star relationships"""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client'
        )
        volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer'
        )
        
        score = get_star_score(volunteer_user, client_user)
        
        self.assertEqual(score, 0)

    def test_get_star_score_client_stars_volunteer(self):
        """Test star score when client stars volunteer"""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client'
        )
        volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer'
        )
        
        # Client stars volunteer
        StarRelation.objects.create(from_user=client_user, to_user=volunteer_user)
        
        score = get_star_score(volunteer_user, client_user)
        
        self.assertEqual(score, 2)

    def test_get_star_score_volunteer_stars_client(self):
        """Test star score when volunteer stars client"""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client'
        )
        volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer'
        )
        
        # Volunteer stars client
        StarRelation.objects.create(from_user=volunteer_user, to_user=client_user)
        
        score = get_star_score(volunteer_user, client_user)
        
        self.assertEqual(score, 1)

    def test_get_star_score_mutual_stars(self):
        """Test star score when both users star each other"""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client'
        )
        volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer'
        )
        
        # Mutual starring
        StarRelation.objects.create(from_user=client_user, to_user=volunteer_user)
        StarRelation.objects.create(from_user=volunteer_user, to_user=client_user)
        
        score = get_star_score(volunteer_user, client_user)
        
        self.assertEqual(score, 3)


class VolunteerMatchingTests(TestCase):
    """Test cases for volunteer matching algorithm"""
    
    def setUp(self):
        # Create support types
        self.shopping_support = SupportType.objects.create(name='Shopping')
        self.cleaning_support = SupportType.objects.create(name='Cleaning')
        
        # Create client user
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        
        # Create client profile with location
        self.client_profile = UserProfile.objects.create(
            user=self.client_user,
            first_name='Jane',
            last_name='Client',
            phone_number='1234567890',
            location='AB12 3CD',
            location_lat=51.5074,
            location_lng=-0.1278,
            eligibility_confirmed=True
        )
        
        ClientProfile.objects.create(
            user_profile=self.client_profile,
            preferred_contact_method='email',
            has_pets=False
        )
        
        # Create volunteer user
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        # Create volunteer profile with location
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='0987654321',
            location='AB12 3CD',
            location_lat=51.5074,
            location_lng=-0.1278,
            eligibility_confirmed=True
        )
        
        self.volunteer_profile_obj = VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student',
            is_scheduled=True,
            available_days=['Monday', 'Tuesday', 'Wednesday'],
            available_start_time=time(9, 0),
            available_end_time=time(17, 0),
            preferred_distance_km=10,
            accept_pets=True,
            max_task_count=5,
            assigned_tasks_count=0
        )
        self.volunteer_profile_obj.preferred_tasks.add(self.shopping_support)
        
        # Create test task
        self.task = Task.objects.create(
            title='Weekly Shopping',
            description='Help with grocery shopping',
            start_time=timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1),
            end_time=timezone.now().replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        self.task.work_area.add(self.shopping_support)

    def test_match_volunteers_successful_match(self):
        """Test successful volunteer matching"""
        # Ensure task is on a Monday (volunteer is available on Monday)
        monday_date = timezone.now().date()
        while monday_date.weekday() != 0:  # 0 = Monday
            monday_date += timedelta(days=1)
        
        self.task.start_time = timezone.datetime.combine(monday_date, time(10, 0))
        self.task.start_time = timezone.make_aware(self.task.start_time)
        self.task.end_time = timezone.datetime.combine(monday_date, time(12, 0))
        self.task.end_time = timezone.make_aware(self.task.end_time)
        self.task.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 1)
        self.assertTrue(TaskApplication.objects.filter(
            task=self.task,
            volunteer=self.volunteer_user,
            is_auto_matched=True
        ).exists())

    def test_match_volunteers_support_type_mismatch(self):
        """Test no match when support types don't match"""
        # Remove shopping support from volunteer's preferred tasks
        self.volunteer_profile_obj.preferred_tasks.clear()
        self.volunteer_profile_obj.preferred_tasks.add(self.cleaning_support)
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)
        self.assertFalse(TaskApplication.objects.filter(
            task=self.task,
            volunteer=self.volunteer_user
        ).exists())

    def test_match_volunteers_day_unavailable(self):
        """Test no match when volunteer is not available on task day"""
        # Set volunteer available only on weekends
        self.volunteer_profile_obj.available_days = ['Saturday', 'Sunday']
        self.volunteer_profile_obj.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)
        self.assertFalse(TaskApplication.objects.filter(
            task=self.task,
            volunteer=self.volunteer_user
        ).exists())

    def test_match_volunteers_time_conflict_start_time(self):
        """Test no match when task starts before volunteer's available time"""
        # Set task to start at 8 AM, but volunteer is available from 9 AM
        early_start = self.task.start_time.replace(hour=8)
        self.task.start_time = early_start
        self.task.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)

    def test_match_volunteers_time_conflict_end_time(self):
        """Test no match when task ends after volunteer's available time"""
        # Set task to end at 6 PM, but volunteer is available until 5 PM
        late_end = self.task.end_time.replace(hour=18)
        self.task.end_time = late_end
        self.task.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)

    def test_match_volunteers_pet_conflict(self):
        """Test no match when client has pets but volunteer doesn't accept pets"""
        # Client has pets, volunteer doesn't accept pets
        client_profile = self.client_user.userprofile.clientprofile
        client_profile.has_pets = True
        client_profile.save()
        
        self.volunteer_profile_obj.accept_pets = False
        self.volunteer_profile_obj.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)

    def test_match_volunteers_distance_too_far(self):
        """Test no match when distance exceeds volunteer's preference"""
        # Set volunteer's preferred distance to 1 km, but client is further away
        self.volunteer_profile_obj.preferred_distance_km = 1
        self.volunteer_profile_obj.save()
        
        # Move client far away (Paris coordinates)
        self.client_profile.location_lat = 48.8566
        self.client_profile.location_lng = 2.3522
        self.client_profile.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)

    def test_match_volunteers_existing_application(self):
        """Test no match when volunteer has already applied"""
        # Create existing application
        TaskApplication.objects.create(
            task=self.task,
            volunteer=self.volunteer_user,
            status='pending'
        )
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)
        # Should still have only one application
        self.assertEqual(TaskApplication.objects.filter(
            task=self.task,
            volunteer=self.volunteer_user
        ).count(), 1)

    def test_match_volunteers_scheduling_conflict(self):
        """Test no match when volunteer has conflicting task"""
        # Create conflicting task
        conflicting_task = Task.objects.create(
            title='Conflicting Task',
            description='Conflicts with main task',
            start_time=self.task.start_time - timedelta(minutes=30),
            end_time=self.task.end_time + timedelta(minutes=30),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        
        # Create accepted application for conflicting task
        TaskApplication.objects.create(
            task=conflicting_task,
            volunteer=self.volunteer_user,
            status='accepted'
        )
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)

    def test_match_volunteers_not_scheduled(self):
        """Test no match when volunteer is not scheduled"""
        self.volunteer_profile_obj.is_scheduled = False
        self.volunteer_profile_obj.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)

    def test_match_volunteers_missing_location_data(self):
        """Test no match when location data is missing"""
        # Remove location data from volunteer
        self.volunteer_profile.location_lat = None
        self.volunteer_profile.location_lng = None
        self.volunteer_profile.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 0)

    def test_match_volunteers_star_priority_sorting(self):
        """Test that volunteers with higher star scores are prioritized"""
        # Create second volunteer
        volunteer2_user = User.objects.create_user(
            email='volunteer2@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        volunteer2_profile = UserProfile.objects.create(
            user=volunteer2_user,
            first_name='Jane',
            last_name='Volunteer2',
            phone_number='1111111111',
            location='AB12 3CD',
            location_lat=51.5074,
            location_lng=-0.1278,
            eligibility_confirmed=True
        )
        
        volunteer2_profile_obj = VolunteerProfile.objects.create(
            user_profile=volunteer2_profile,
            university_course='Engineering',
            profession='Student',
            is_scheduled=True,
            available_days=['Monday', 'Tuesday', 'Wednesday'],
            available_start_time=time(9, 0),
            available_end_time=time(17, 0),
            preferred_distance_km=10,
            accept_pets=True,
            max_task_count=5,
            assigned_tasks_count=0
        )
        volunteer2_profile_obj.preferred_tasks.add(self.shopping_support)
        
        # Give volunteer2 higher star score
        StarRelation.objects.create(from_user=self.client_user, to_user=volunteer2_user)
        
        # Increase vol_number to allow both volunteers
        self.task.vol_number = 2
        self.task.save()
        
        # Ensure task is on Monday
        monday_date = timezone.now().date()
        while monday_date.weekday() != 0:
            monday_date += timedelta(days=1)
        
        self.task.start_time = timezone.datetime.combine(monday_date, time(10, 0))
        self.task.start_time = timezone.make_aware(self.task.start_time)
        self.task.end_time = timezone.datetime.combine(monday_date, time(12, 0))
        self.task.end_time = timezone.make_aware(self.task.end_time)
        self.task.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 2)
        
        # Check that both volunteers were matched
        applications = TaskApplication.objects.filter(task=self.task).order_by('id')
        self.assertEqual(applications.count(), 2)

    def test_match_volunteers_max_task_count_reached(self):
        """Test that volunteer is disabled when max task count is reached"""
        # Set volunteer to be at max task count - 1
        self.volunteer_profile_obj.assigned_tasks_count = 4
        self.volunteer_profile_obj.max_task_count = 5
        self.volunteer_profile_obj.save()
        
        # Ensure task is on Monday
        monday_date = timezone.now().date()
        while monday_date.weekday() != 0:
            monday_date += timedelta(days=1)
        
        self.task.start_time = timezone.datetime.combine(monday_date, time(10, 0))
        self.task.start_time = timezone.make_aware(self.task.start_time)
        self.task.end_time = timezone.datetime.combine(monday_date, time(12, 0))
        self.task.end_time = timezone.make_aware(self.task.end_time)
        self.task.save()
        
        matched_count = match_volunteers_for_task(self.task)
        
        self.assertEqual(matched_count, 1)
        
        # Check that volunteer is now disabled for scheduling
        self.volunteer_profile_obj.refresh_from_db()
        self.assertFalse(self.volunteer_profile_obj.is_scheduled)
        self.assertEqual(self.volunteer_profile_obj.assigned_tasks_count, 5)


class VolunteerAvailabilityFormTests(TestCase):
    """Test cases for VolunteerAvailabilityForm"""
    
    def setUp(self):
        self.support_type = SupportType.objects.create(name='Shopping')
        
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='0987654321',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        
        self.volunteer_profile_obj = VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )

    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'is_scheduled': True,
            'available_days': ['Monday', 'Tuesday', 'Wednesday'],
            'available_start_time': '09:00',
            'available_end_time': '17:00',
            'preferred_tasks': [self.support_type.id],
            'preferred_distance_km': 10,
            'accept_pets': True,
            'max_task_count': 5
        }
        
        form = VolunteerAvailabilityForm(data=form_data, instance=self.volunteer_profile_obj)
        
        self.assertTrue(form.is_valid())

    def test_form_save(self):
        """Test form saves data correctly"""
        form_data = {
            'is_scheduled': True,
            'available_days': ['Monday', 'Wednesday', 'Friday'],
            'available_start_time': '10:00',
            'available_end_time': '16:00',
            'preferred_tasks': [self.support_type.id],
            'preferred_distance_km': 15,
            'accept_pets': False,
            'max_task_count': 3
        }
        
        form = VolunteerAvailabilityForm(data=form_data, instance=self.volunteer_profile_obj)
        
        self.assertTrue(form.is_valid())
        saved_instance = form.save()
        
        self.assertTrue(saved_instance.is_scheduled)
        self.assertEqual(saved_instance.available_days, ['Monday', 'Wednesday', 'Friday'])
        self.assertEqual(saved_instance.available_start_time.strftime('%H:%M'), '10:00')
        self.assertEqual(saved_instance.available_end_time.strftime('%H:%M'), '16:00')
        self.assertEqual(saved_instance.preferred_distance_km, 15)
        self.assertFalse(saved_instance.accept_pets)
        self.assertEqual(saved_instance.max_task_count, 3)

    def test_form_empty_available_days(self):
        """Test form with empty available days (should be valid as it's not required)"""
        form_data = {
            'is_scheduled': False,
            'available_days': [],
            'preferred_tasks': [self.support_type.id],
            'preferred_distance_km': 10,
            'accept_pets': True,
            'max_task_count': 5
        }
        
        form = VolunteerAvailabilityForm(data=form_data, instance=self.volunteer_profile_obj)
        
        self.assertTrue(form.is_valid())

    def test_form_invalid_time_range(self):
        """Test form validation doesn't prevent invalid time ranges (handled by model)"""
        form_data = {
            'is_scheduled': True,
            'available_days': ['Monday'],
            'available_start_time': '17:00',  # Start after end
            'available_end_time': '09:00',
            'preferred_tasks': [self.support_type.id],
            'preferred_distance_km': 10,
            'accept_pets': True,
            'max_task_count': 5
        }
        
        form = VolunteerAvailabilityForm(data=form_data, instance=self.volunteer_profile_obj)
        
        # Form validation should pass (business logic validation would be in model/view)
        self.assertTrue(form.is_valid())


class MatchingViewTests(TestCase):
    """Test cases for matching views"""
    
    def setUp(self):
        self.support_type = SupportType.objects.create(name='Shopping')
        
        # Create volunteer user
        self.volunteer_user = User.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer',
            is_active=True
        )
        
        # Create client user (for testing access control)
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        
        # Create volunteer profile
        self.volunteer_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='John',
            last_name='Volunteer',
            phone_number='0987654321',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        
        # Create client profile (for testing access control)
        self.client_profile = UserProfile.objects.create(
            user=self.client_user,
            first_name='Jane',
            last_name='Client',
            phone_number='1234567890',
            location='AB12 3CD',
            eligibility_confirmed=True
        )
        
        self.volunteer_profile_obj = VolunteerProfile.objects.create(
            user_profile=self.volunteer_profile,
            university_course='Computer Science',
            profession='Student'
        )
        
        ClientProfile.objects.create(
            user_profile=self.client_profile,
            preferred_contact_method='email'
        )
        
        self.client = Client()

    def test_shift_view_get_volunteer_access(self):
        """Test that volunteers can access the shift settings page"""
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('matching:shift'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Setting Scheduling Intentions')
        self.assertIsInstance(response.context['form'], VolunteerAvailabilityForm)

    def test_shift_view_client_forbidden(self):
        """Test that clients cannot access volunteer shift settings"""
        self.client.login(email='client@test.com', password='testpass123')
        response = self.client.get(reverse('matching:shift'))
        
        self.assertEqual(response.status_code, 403)

    def test_shift_view_anonymous_redirect(self):
        """Test that anonymous users are redirected to login"""
        response = self.client.get(reverse('matching:shift'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_shift_view_post_valid_data(self):
        """Test successful form submission"""
        self.client.login(email='volunteer@test.com', password='testpass123')
        
        form_data = {
            'is_scheduled': True,
            'available_days': ['Monday', 'Wednesday', 'Friday'],
            'available_start_time': '09:00',
            'available_end_time': '17:00',
            'preferred_tasks': [self.support_type.id],
            'preferred_distance_km': 10,
            'accept_pets': True,
            'max_task_count': 5
        }
        
        response = self.client.post(reverse('matching:shift'), form_data)
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful save
        self.assertRedirects(response, reverse('user:home'))
        
        # Check that data was saved
        self.volunteer_profile_obj.refresh_from_db()
        self.assertTrue(self.volunteer_profile_obj.is_scheduled)
        self.assertEqual(self.volunteer_profile_obj.available_days, ['Monday', 'Wednesday', 'Friday'])

    def test_shift_view_post_invalid_data(self):
        """Test form submission with invalid data"""
        self.client.login(email='volunteer@test.com', password='testpass123')
        
        # Submit form with missing required fields
        form_data = {
            'is_scheduled': True,
            # Missing other required fields
        }
        
        response = self.client.post(reverse('matching:shift'), form_data)
        
        self.assertEqual(response.status_code, 200)  # Stay on form page
        self.assertIsInstance(response.context['form'], VolunteerAvailabilityForm)
        self.assertFalse(response.context['form'].is_valid())

    def test_shift_view_form_instance_binding(self):
        """Test that form is properly bound to volunteer profile instance"""
        # Set some initial data
        self.volunteer_profile_obj.is_scheduled = True
        self.volunteer_profile_obj.available_days = ['Tuesday', 'Thursday']
        self.volunteer_profile_obj.preferred_distance_km = 15
        self.volunteer_profile_obj.save()
        
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('matching:shift'))
        
        form = response.context['form']
        self.assertEqual(form.instance, self.volunteer_profile_obj)
        self.assertTrue(form.initial.get('is_scheduled'))
        self.assertEqual(form.initial.get('available_days'), ['Tuesday', 'Thursday'])
        self.assertEqual(form.initial.get('preferred_distance_km'), 15)

    @patch('matching.views.OperationLog.objects.create')
    def test_shift_view_operation_log_creation(self, mock_log_create):
        """Test that operation log is created when settings are saved"""
        self.client.login(email='volunteer@test.com', password='testpass123')
        
        form_data = {
            'is_scheduled': True,
            'available_days': ['Monday'],
            'available_start_time': '09:00',
            'available_end_time': '17:00',
            'preferred_tasks': [self.support_type.id],
            'preferred_distance_km': 10,
            'accept_pets': True,
            'max_task_count': 5
        }
        
        response = self.client.post(reverse('matching:shift'), form_data)
        
        self.assertEqual(response.status_code, 302)
        mock_log_create.assert_called_once()
        
        # Check the log entry details
        call_args = mock_log_create.call_args
        self.assertEqual(call_args[1]['user'], self.volunteer_user)
        self.assertIn('shift', call_args[1]['action'])


class MatchingIntegrationTests(TestCase):
    """Integration tests for the complete matching workflow"""
    
    def setUp(self):
        # Create support types
        self.shopping_support = SupportType.objects.create(name='Shopping')
        self.cleaning_support = SupportType.objects.create(name='Cleaning')
        
        # Create client
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        
        self.client_profile = UserProfile.objects.create(
            user=self.client_user,
            first_name='Jane',
            last_name='Client',
            phone_number='1234567890',
            location='AB12 3CD',
            location_lat=51.5074,
            location_lng=-0.1278,
            eligibility_confirmed=True
        )
        
        ClientProfile.objects.create(
            user_profile=self.client_profile,
            preferred_contact_method='email',
            has_pets=False
        )
        
        # Create multiple volunteers
        self.volunteers = []
        for i in range(3):
            volunteer_user = User.objects.create_user(
                email=f'volunteer{i}@test.com',
                password='testpass123',
                role='volunteer',
                is_active=True
            )
            
            volunteer_profile = UserProfile.objects.create(
                user=volunteer_user,
                first_name=f'Volunteer{i}',
                last_name='Test',
                phone_number=f'098765432{i}',
                location='AB12 3CD',
                location_lat=51.5074,
                location_lng=-0.1278,
                eligibility_confirmed=True
            )
            
            volunteer_profile_obj = VolunteerProfile.objects.create(
                user_profile=volunteer_profile,
                university_course='Computer Science',
                profession='Student',
                is_scheduled=True,
                available_days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                available_start_time=time(9, 0),
                available_end_time=time(17, 0),
                preferred_distance_km=10,
                accept_pets=True,
                max_task_count=5,
                assigned_tasks_count=0
            )
            volunteer_profile_obj.preferred_tasks.add(self.shopping_support)
            
            self.volunteers.append({
                'user': volunteer_user,
                'profile': volunteer_profile,
                'volunteer_profile': volunteer_profile_obj
            })
        
        self.client = Client()

    def test_complete_matching_workflow(self):
        """Test complete workflow from volunteer setup to task matching"""
        # Step 1: Volunteer sets up availability
        volunteer = self.volunteers[0]
        self.client.login(email=volunteer['user'].email, password='testpass123')
        
        form_data = {
            'is_scheduled': True,
            'available_days': ['Monday', 'Wednesday', 'Friday'],
            'available_start_time': '10:00',
            'available_end_time': '16:00',
            'preferred_tasks': [self.shopping_support.id],
            'preferred_distance_km': 15,
            'accept_pets': True,
            'max_task_count': 3
        }
        
        response = self.client.post(reverse('matching:shift'), form_data)
        self.assertEqual(response.status_code, 302)
        
        # Step 2: Create task that matches volunteer's availability
        monday_date = timezone.now().date()
        while monday_date.weekday() != 0:  # Find next Monday
            monday_date += timedelta(days=1)
        
        task = Task.objects.create(
            title='Monday Shopping Task',
            description='Weekly grocery shopping',
            start_time=timezone.datetime.combine(monday_date, time(11, 0)),
            end_time=timezone.datetime.combine(monday_date, time(13, 0)),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        task.start_time = timezone.make_aware(task.start_time)
        task.end_time = timezone.make_aware(task.end_time)
        task.save()
        task.work_area.add(self.shopping_support)
        
        # Step 3: Run matching algorithm
        matched_count = match_volunteers_for_task(task)
        
        self.assertEqual(matched_count, 1)
        
        # Step 4: Verify application was created
        application = TaskApplication.objects.get(task=task, volunteer=volunteer['user'])
        self.assertEqual(application.status, 'pending')
        self.assertTrue(application.is_auto_matched)
        
        # Step 5: Verify volunteer's task count was updated
        volunteer['volunteer_profile'].refresh_from_db()
        self.assertEqual(volunteer['volunteer_profile'].assigned_tasks_count, 1)

    def test_multiple_volunteers_star_priority(self):
        """Test matching with multiple volunteers and star priority"""
        # Give different star scores to volunteers
        StarRelation.objects.create(
            from_user=self.client_user, 
            to_user=self.volunteers[1]['user']  # Volunteer 1 gets 2 points
        )
        StarRelation.objects.create(
            from_user=self.volunteers[2]['user'], 
            to_user=self.client_user  # Volunteer 2 gets 1 point
        )
        # Volunteer 0 gets 0 points
        
        # Create task that needs 2 volunteers
        monday_date = timezone.now().date()
        while monday_date.weekday() != 0:
            monday_date += timedelta(days=1)
        
        task = Task.objects.create(
            title='Multi-Volunteer Task',
            description='Task requiring multiple volunteers',
            start_time=timezone.datetime.combine(monday_date, time(10, 0)),
            end_time=timezone.datetime.combine(monday_date, time(12, 0)),
            vol_number=2,
            client=self.client_user,
            status='open'
        )
        task.start_time = timezone.make_aware(task.start_time)
        task.end_time = timezone.make_aware(task.end_time)
        task.save()
        task.work_area.add(self.shopping_support)
        
        matched_count = match_volunteers_for_task(task)
        
        self.assertEqual(matched_count, 2)
        
        # Check that volunteers with higher star scores were selected
        applications = TaskApplication.objects.filter(task=task)
        matched_volunteers = [app.volunteer for app in applications]
        
        # Volunteer 1 (2 points) and Volunteer 2 (1 point) should be matched
        self.assertIn(self.volunteers[1]['user'], matched_volunteers)
        self.assertIn(self.volunteers[2]['user'], matched_volunteers)
        # Volunteer 0 (0 points) should not be matched
        self.assertNotIn(self.volunteers[0]['user'], matched_volunteers)

    def test_volunteer_reaches_max_task_limit(self):
        """Test that volunteer is disabled when reaching max task limit"""
        volunteer = self.volunteers[0]
        
        # Set volunteer to be one task away from limit
        volunteer['volunteer_profile'].assigned_tasks_count = 4
        volunteer['volunteer_profile'].max_task_count = 5
        volunteer['volunteer_profile'].save()
        
        # Create task
        monday_date = timezone.now().date()
        while monday_date.weekday() != 0:
            monday_date += timedelta(days=1)
        
        task = Task.objects.create(
            title='Final Task',
            description='Task that will reach volunteer limit',
            start_time=timezone.datetime.combine(monday_date, time(10, 0)),
            end_time=timezone.datetime.combine(monday_date, time(12, 0)),
            vol_number=1,
            client=self.client_user,
            status='open'
        )
        task.start_time = timezone.make_aware(task.start_time)
        task.end_time = timezone.make_aware(task.end_time)
        task.save()
        task.work_area.add(self.shopping_support)
        
        matched_count = match_volunteers_for_task(task)
        
        self.assertEqual(matched_count, 1)
        
        # Check that volunteer is now disabled and at max count
        volunteer['volunteer_profile'].refresh_from_db()
        self.assertFalse(volunteer['volunteer_profile'].is_scheduled)
        self.assertEqual(volunteer['volunteer_profile'].assigned_tasks_count, 5)
