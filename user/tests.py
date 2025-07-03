# user/test.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import CustomUser, UserProfile, ClientProfile, VolunteerProfile, CertificationType, ConditionType, SupportType
from .forms import ClientRegisterForm, ClientProfileForm, VolunteerRegisterForm, VolunteerProfileForm, ProfilePhotoForm
import json
import base64
from django.test.utils import override_settings
from django.core.files.storage import FileSystemStorage

@override_settings(STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage', DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class CustomUserModelTests(TestCase):
    def setUp(self):
        self.user_manager = CustomUser.objects
        self.client_user = self.user_manager.create_user(
            email='client@test.com',
            password='testpass123',
            role='client'
        )
        self.volunteer_user = self.user_manager.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer'
        )
        self.user_profile_client = UserProfile.objects.create(
            user=self.client_user,
            first_name='Client',
            last_name='Test',
            phone_number='1234567890',
            location='Test City',
            consent_safeguard=True
        )
        self.user_profile_volunteer = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='Volunteer',
            last_name='Test',
            phone_number='0987654321',
            location='Test City',
            consent_safeguard=True
        )
        self.cert_type = CertificationType.objects.create(name='PIP')
        self.condition_type = ConditionType.objects.create(name='Diabetes')
        self.support_type = SupportType.objects.create(name='Medical Assistance')
        self.client_profile = ClientProfile.objects.create(
            user_profile=self.user_profile_client,
            preferred_contact_method='email'
        )
        self.client_profile.certifications.add(self.cert_type)
        self.client_profile.conditions.add(self.condition_type)
        self.client_profile.support_areas.add(self.support_type)
        self.volunteer_profile = VolunteerProfile.objects.create(
            user_profile=self.user_profile_volunteer,
            university_course='Computer Science',
            profession='Student',
            is_for_credit=False
        )

    def test_custom_user_creation(self):
        user = self.user_manager.create_user(
            email='testuser@test.com',
            password='testpass123',
            role='client'
        )
        self.assertEqual(user.email, 'testuser@test.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.role, 'client')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_superuser_creation(self):
        superuser = self.user_manager.create_superuser(
            email='admin@test.com',
            password='adminpass123'
        )
        self.assertEqual(superuser.email, 'admin@test.com')
        self.assertTrue(superuser.check_password('adminpass123'))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_str(self):
        self.assertEqual(str(self.client_user), 'client@test.com')

    def test_whether_in_task(self):
        self.assertFalse(self.client_user.whether_in_task(1))
        self.assertFalse(self.volunteer_user.whether_in_task(1))

    def test_user_profile_creation(self):
        self.assertEqual(self.user_profile_client.first_name, 'Client')
        self.assertEqual(self.user_profile_client.phone_number, '1234567890')

    def test_client_profile_creation(self):
        self.assertEqual(self.client_profile.preferred_contact_method, 'email')
        self.assertTrue(self.client_profile.certifications.filter(name='PIP').exists())

    def test_volunteer_profile_creation(self):
        self.assertEqual(self.volunteer_profile.university_course, 'Computer Science')
        self.assertFalse(self.volunteer_profile.is_for_credit)


@override_settings(STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage', DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class ClientRegisterFormTests(TestCase):
    def setUp(self):
        self.cert_type = CertificationType.objects.create(name='PIP')
        self.form_data = {
            'email': 'newclient@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'Client',
            'phone_number': '1234567890',
            'contact_method': 'email',
            'location': 'Test City',
            'certifications': [self.cert_type.id],
            'consent_safeguard': True
        }

    def test_client_register_form_valid(self):
        form = ClientRegisterForm(data=self.form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, 'newclient@test.com')
        self.assertEqual(user.role, 'client')
        self.assertEqual(user.userprofile.first_name, 'New')
        self.assertEqual(user.userprofile.clientprofile.preferred_contact_method, 'email')
        self.assertTrue(user.userprofile.clientprofile.certifications.filter(name='PIP').exists())

    def test_client_register_form_missing_consent(self):
        invalid_data = self.form_data.copy()
        invalid_data['consent_safeguard'] = False
        form = ClientRegisterForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('consent_safeguard', form.errors)


@override_settings(STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage', DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class VolunteerRegisterFormTests(TestCase):
    def setUp(self):
        self.form_data = {
            'email': 'newvolunteer@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'Volunteer',
            'phone_number': '0987654321',
            'location': 'Test City',
            'university_course': 'Biology',
            'profession': 'Student',
            'is_for_credit': False,
            'consent_safeguard': True
        }

    def test_volunteer_register_form_valid(self):
        form = VolunteerRegisterForm(data=self.form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, 'newvolunteer@test.com')
        self.assertEqual(user.role, 'volunteer')
        self.assertEqual(user.userprofile.first_name, 'New')
        self.assertEqual(user.userprofile.volunteerprofile.university_course, 'Biology')

    def test_volunteer_register_form_missing_consent(self):
        invalid_data = self.form_data.copy()
        invalid_data['consent_safeguard'] = False
        form = VolunteerRegisterForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('consent_safeguard', form.errors)


@override_settings(STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage', DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class ClientProfileFormTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='client@test.com',
            password='testpass123',
            role='client'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Client',
            last_name='Test',
            phone_number='1234567890',
            location='Test City'
        )
        self.cert_type = CertificationType.objects.create(name='PIP')
        self.condition_type = ConditionType.objects.create(name='Diabetes')
        self.support_type = SupportType.objects.create(name='Medical Assistance')
        self.client_profile = ClientProfile.objects.create(
            user_profile=self.user_profile,
            preferred_contact_method='email'
        )
        self.client_profile.certifications.add(self.cert_type)
        self.form_data = {
            'conditions': [self.condition_type.id],
            'support_areas': [self.support_type.id],
            'age': '18-24',
            'gender': 'male',
            'has_pets': False,
            'pets_type': '',
            'emergency_contact': 'Emergency Contact',
            'preferred_times': '{"Monday": ["09:00-11:00"]}',
            'allergies': 'None',
            'dietary_needs': 'Vegetarian',
            'other_conditions': '',
            'other_support': '',
            'pip_certificate': SimpleUploadedFile('pip.pdf', b'file_content', content_type='application/pdf')
        }

    def test_client_profile_form_valid(self):
        form = ClientProfileForm(data=self.form_data, instance=self.client_profile)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.user_profile.age = self.form_data['age']
        self.user_profile.gender = self.form_data['gender']
        self.user_profile.emergency_contact = self.form_data['emergency_contact']
        self.user_profile.save()
        self.user_profile.refresh_from_db()
        self.client_profile.refresh_from_db()
        self.assertEqual(self.user_profile.age, '18-24')
        self.assertEqual(self.user_profile.gender, 'male')
        self.assertEqual(self.user_profile.emergency_contact, 'Emergency Contact')
        self.assertTrue(self.client_profile.conditions.filter(name='Diabetes').exists())
        self.assertTrue(self.client_profile.support_areas.filter(name='Medical Assistance').exists())
        self.assertIsNotNone(self.client_profile.pip_certificate)

    def test_client_profile_form_dynamic_fields(self):
        form = ClientProfileForm(instance=self.client_profile)
        self.assertIn('pip_certificate', form.fields)


@override_settings(STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage', DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class VolunteerProfileFormTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Volunteer',
            last_name='Test',
            phone_number='0987654321',
            location='Test City'
        )
        self.support_type = SupportType.objects.create(name='Medical Assistance')
        self.volunteer_profile = VolunteerProfile.objects.create(
            user_profile=self.user_profile,
            university_course='Biology',
            profession='Student'
        )
        self.form_data = {
            'skills': 'First Aid',
            'interests': 'Helping others',
            'preferred_tasks': [self.support_type.id],
            'pvg_level': 'pending',
            'pvg_file': SimpleUploadedFile('pvg.pdf', b'file_content', content_type='application/pdf'),
            'availability': '{"Monday": ["09:00-11:00"]}',
            'motivation': 'To give back to the community',
            'age': '18-24',
            'gender': 'Female',
            'emergency_contact': 'Emergency Contact'
        }

    def test_volunteer_profile_form_valid(self):
        form = VolunteerProfileForm(data=self.form_data, instance=self.volunteer_profile)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.user_profile.age = self.form_data['age']
        self.user_profile.gender = self.form_data['gender']
        self.user_profile.emergency_contact = self.form_data['emergency_contact']
        self.user_profile.save()
        self.user_profile.refresh_from_db()
        self.volunteer_profile.refresh_from_db()
        self.assertEqual(self.user_profile.age, '18-24')
        self.assertEqual(self.user_profile.gender, 'Female')
        self.assertEqual(self.volunteer_profile.skills, 'First Aid')
        self.assertTrue(self.volunteer_profile.preferred_tasks.filter(name='Medical Assistance').exists())
        self.assertIsNotNone(self.volunteer_profile.pvg_file)


@override_settings(STATICFILES_STORAGE='django.core.files.storage.FileSystemStorage', DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class UserViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='testuser@test.com',
            password='testpass123',
            role='client'
        )
        self.client_user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            phone_number='1234567890',
            location='Test City'
        )
        self.client_profile = ClientProfile.objects.create(
            user_profile=self.client_user_profile,
            preferred_contact_method='email'
        )
        self.volunteer_user = CustomUser.objects.create_user(
            email='volunteer@test.com',
            password='testpass123',
            role='volunteer'
        )
        self.volunteer_user_profile = UserProfile.objects.create(
            user=self.volunteer_user,
            first_name='Volunteer',
            last_name='User',
            phone_number='0987654321',
            location='Test City'
        )
        self.volunteer_profile = VolunteerProfile.objects.create(
            user_profile=self.volunteer_user_profile,
            university_course='Biology',
            profession='Student'
        )

    def test_home_view(self):
        response = self.client.get(reverse('user:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/home.html')

    def test_login_view_get(self):
        response = self.client.get(reverse('user:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/login.html')

    def test_login_view_post_success(self):
        response = self.client.post(reverse('user:login'), {
            'username': 'testuser@test.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('user:home'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_view_post_failure(self):
        response = self.client.post(reverse('user:login'), {
            'username': 'testuser@test.com',
            'password': 'wrongpassword'
        })
        self.assertRedirects(response, reverse('user:login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_view(self):
        self.client.login(email='testuser@test.com', password='testpass123')
        response = self.client.get(reverse('user:logout'))
        self.assertRedirects(response, reverse('user:login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_client_register_view_get(self):
        response = self.client.get(reverse('user:client_register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/client_register.html')

    def test_client_register_view_post(self):
        cert_type = CertificationType.objects.create(name='PIP')
        response = self.client.post(reverse('user:client_register'), {
            'email': 'newclient@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'Client',
            'phone_number': '1234567890',
            'contact_method': 'email',
            'location': 'Test City',
            'certifications': [cert_type.id],
            'consent_safeguard': True
        })
        self.assertRedirects(response, reverse('user:home'))
        self.assertTrue(CustomUser.objects.filter(email='newclient@test.com').exists())

    def test_volunteer_register_view_get(self):
        response = self.client.get(reverse('user:volunteer_register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/volunteer_register.html')

    def test_volunteer_register_view_post(self):
        response = self.client.post(reverse('user:volunteer_register'), {
            'email': 'newvolunteer@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'Volunteer',
            'phone_number': '0987654321',
            'location': 'Test City',
            'university_course': 'Biology',
            'profession': 'Student',
            'is_for_credit': False,
            'consent_safeguard': True
        })
        self.assertRedirects(response, reverse('user:home'))
        self.assertTrue(CustomUser.objects.filter(email='newvolunteer@test.com').exists())

    def test_client_profile_edit_view_get(self):
        self.client.login(email='testuser@test.com', password='testpass123')
        response = self.client.get(reverse('user:client_profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/client_profile_edit.html')

    def test_client_profile_edit_view_post(self):
        self.client.login(email='testuser@test.com', password='testpass123')
        cert_type = CertificationType.objects.create(name='PIP')
        condition_type = ConditionType.objects.create(name='Diabetes')
        support_type = SupportType.objects.create(name='Medical Assistance')
        response = self.client.post(reverse('user:client_profile_edit'), {
            'conditions': [condition_type.id],
            'support_areas': [support_type.id],
            'age': '18-24',
            'gender': 'male',
            'has_pets': False,
            'pets_type': '',
            'emergency_contact': 'Emergency Contact',
            'preferred_times': '{"Monday": ["09:00-11:00"]}',
            'allergies': 'None',
            'dietary_needs': 'Vegetarian',
            'other_conditions': '',
            'other_support': '',
            'pip_certificate': SimpleUploadedFile('pip.pdf', b'file_content', content_type='application/pdf')
        })
        self.assertRedirects(response, reverse('user:profile_detail'))
        self.client_user_profile.refresh_from_db()
        self.client_profile.refresh_from_db()
        self.assertEqual(self.client_user_profile.age, '18-24')
        self.assertTrue(self.client_profile.conditions.filter(name='Diabetes').exists())

    def test_volunteer_profile_edit_view_get(self):
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('user:volunteer_profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/volunteer_profile_edit.html')

    def test_volunteer_profile_edit_view_post(self):
        self.client.login(email='volunteer@test.com', password='testpass123')
        support_type = SupportType.objects.create(name='Medical Assistance')
        response = self.client.post(reverse('user:volunteer_profile_edit'), {
            'skills': 'First Aid',
            'interests': 'Helping others',
            'preferred_tasks': [support_type.id],
            'pvg_level': 'pending',
            'pvg_file': SimpleUploadedFile('pvg.pdf', b'file_content', content_type='application/pdf'),
            'availability': '{"Monday": ["09:00-11:00"]}',
            'motivation': 'To give back',
            'age': '18-24',
            'gender': 'Female',
            'emergency_contact': 'Emergency Contact'
        })
        self.assertRedirects(response, reverse('user:profile_detail'))
        self.volunteer_profile.refresh_from_db()
        self.assertEqual(self.volunteer_profile.skills, 'First Aid')

    def test_profile_detail_view_client(self):
        self.client.login(email='testuser@test.com', password='testpass123')
        response = self.client.get(reverse('user:profile_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/profile_detail.html')
        self.assertIn('client_profile', response.context)

    def test_profile_detail_view_volunteer(self):
        self.client.login(email='volunteer@test.com', password='testpass123')
        response = self.client.get(reverse('user:profile_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/profile_detail.html')
        self.assertIn('volunteer_profile', response.context)

    def test_photo_edit_view_get(self):
        self.client.login(email='testuser@test.com', password='testpass123')
        response = self.client.get(reverse('user:photo_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/photo_edit.html')

    def test_photo_edit_view_post(self):
        self.client.login(email='testuser@test.com', password='testpass123')
        response = self.client.post(reverse('user:photo_edit'), {
            'profile_photo': SimpleUploadedFile('photo.jpg', b'file_content', content_type='image/jpeg')
        })
        self.assertRedirects(response, reverse('user:profile_detail'))
        self.client_user_profile.refresh_from_db()
        self.assertTrue(self.client_user_profile.profile_photo.name)

    def test_save_preferred_times_view_client(self):
        self.client.login(email='testuser@test.com', password='testpass123')
        data = {'Monday': ['09:00-11:00']}
        response = self.client.post(
            reverse('user:save_preferred_times'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success'})
        self.client_profile.refresh_from_db()
        self.assertEqual(self.client_profile.preferred_times, data)

    def test_save_preferred_times_view_volunteer(self):
        self.client.login(email='volunteer@test.com', password='testpass123')
        data = {'Monday': ['09:00-11:00']}
        response = self.client.post(
            reverse('user:save_preferred_times'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success'})
        self.volunteer_profile.refresh_from_db()
        self.assertEqual(self.volunteer_profile.availability, data)