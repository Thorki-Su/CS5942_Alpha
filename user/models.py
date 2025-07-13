from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=[
        ('client', 'Client'),
        ('volunteer', 'Volunteer'),
        ('admin', 'Admin'),
    ])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def whether_in_task(self, task_id):
        from task.models import Task, TaskApplication
        if self.role == 'client':
            return Task.objects.filter(client=self, id=task_id).exists()
        elif self.role == 'volunteer':
            return TaskApplication.objects.filter(volunteer=self, task_id=task_id, status='accepted').exists()
        return False

def user_directory_path(instance, filename):
    return f'profile_photos/{instance.user.email}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    profile_photo = models.ImageField(upload_to=user_directory_path, null=True, blank=True)
    emergency_contact = models.CharField(max_length=255, null=True, blank=True)
    consent_safeguard = models.BooleanField(default=False)

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class CertificationType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class ConditionType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class SupportType(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class ClientProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    certifications = models.ManyToManyField(CertificationType)
    pip_certificate = models.FileField(upload_to='certificates/pip/', null=True, blank=True)
    adp_certificate = models.FileField(upload_to='certificates/adp/', null=True, blank=True)
    lwc_certificate = models.FileField(upload_to='certificates/lwc/', null=True, blank=True)
    nhs_certificate = models.FileField(upload_to='certificates/nhs/', null=True, blank=True)
    diagnosis = models.FileField(upload_to='certificates/diagnosis/', null=True, blank=True)
    eligibility_confirmed = models.BooleanField(default=False)
    preferred_contact_method = models.CharField(max_length=20, choices=[('phone', 'Phone'), ('email', 'Email')])
    conditions = models.ManyToManyField(ConditionType, blank=True)
    other_conditions = models.CharField(max_length=255, null=True, blank=True)
    support_areas = models.ManyToManyField(SupportType, blank=True)
    other_support = models.CharField(max_length=255, null=True, blank=True)
    preferred_times = models.JSONField(default=dict, blank=True)
    allergies = models.TextField(null=True, blank=True)
    dietary_needs = models.TextField(null=True, blank=True)
    has_pets = models.BooleanField(default=False)
    pets_type = models.CharField(max_length=100, null=True, blank=True)

class VolunteerProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    university_course = models.CharField(max_length=255, null=True, blank=True)
    profession = models.CharField(max_length=255, null=True, blank=True)
    is_for_credit = models.BooleanField(default=False)
    skills = models.TextField(null=True, blank=True)
    interests = models.TextField(null=True, blank=True)
    pvg_level = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('verified', 'Verified'),
        ('processing', 'Processing'),
        ('pending', 'Pending'),
        ('do_not_have', 'I do not have a PVG yet'),
    ])
    pvg_file = models.FileField(upload_to='pvg/', null=True, blank=True)
    availability = models.JSONField(default=dict, blank=True)
    motivation = models.TextField(null=True, blank=True)
    preferred_tasks = models.ManyToManyField(SupportType, blank=True)

class AdminProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    area_to_focus = models.CharField(max_length=255, null=True, blank=True)
    project_goal = models.TextField(null=True, blank=True)
    expected_hours = models.CharField(max_length=255, null=True, blank=True)
    supervisor_contact = models.CharField(max_length=255, null=True, blank=True)
    consent_data_use = models.BooleanField(default=False)
    agreement_ethics = models.BooleanField(default=False)