from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from .utils import geocode_address

# For custom CustomUser (use email instead of username)
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
    is_active = models.BooleanField(default=False) # Control whether account is activated (consider if needed)
    is_staff = models.BooleanField(default=False) # Control account access to admin backend

    USERNAME_FIELD = 'email'                      # Specify email as login identifier (replace username)
    REQUIRED_FIELDS = []                          # Fields required when creating user

    objects = CustomUserManager()                 # Bind CustomUserManager as manager for this model

    def __str__(self):
        return self.email
    
    def whether_in_task(self, task_id):           # Check if this user is in the specified task
        from task.models import Task, TaskApplication
        if self.role == 'client':
            return Task.objects.filter(client=self, id=task_id).exists()
        elif self.role == 'volunteer':
            return TaskApplication.objects.filter(volunteer=self, task_id=task_id, status='accepted').exists()
        return False

def user_directory_path(instance, filename):
    return f'profile_photos/{instance.user.email}/{filename}'

# Used to store information common to different users
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255)                                             # Geographic location or postal code
    location_lat = models.FloatField(null=True, blank=True)                                 # Coordinates obtained from geographic location, no need to fill manually
    location_lng = models.FloatField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to=user_directory_path, null=True, blank=True) # Personal photo, used as avatar and display during matching
    emergency_contact = models.CharField(max_length=255, null=True, blank=True)             # Emergency contact (name + contact info)
    eligibility_confirmed = models.BooleanField(default=False)                              # Changed to True after approval
    consent_safeguard = models.BooleanField(default=False)                                  # Whether to agree to data use and security protocol (uncertain if necessary)

    def __str__(self):
        return f"{self.get_full_name} [{self.user.email}]"
    
    def save(self, *args, **kwargs):
        if self.location and (self.location_lat is None or self.location_lng is None):
            lat, lng = geocode_address(self.location)
            if lat and lng:
                self.location_lat = lat
                self.location_lng = lng
        super().save(*args, **kwargs)
    
    @property
    def get_full_name(self): # Get full name
        return f"{self.first_name} {self.last_name}"

# Store welfare certification information
class CertificationType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

# Medical condition
class ConditionType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

# Support area
class SupportType(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

# Store Client-specific information
class ClientProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    certifications = models.ManyToManyField(CertificationType)                               # Whether has PIP, ADP, LWC certifications (many-to-many)
    pip_certificate = models.FileField(upload_to='certificates/pip/', null=True, blank=True) # If certified, client needs to upload
    adp_certificate = models.FileField(upload_to='certificates/adp/', null=True, blank=True)
    lwc_certificate = models.FileField(upload_to='certificates/lwc/', null=True, blank=True)
    nhs_certificate = models.FileField(upload_to='certificates/nhs/', null=True, blank=True)
    diagnosis = models.FileField(upload_to='certificates/diagnosis/', null=True, blank=True)
    preferred_contact_method = models.CharField(max_length=20, choices=[('phone', 'Phone'), ('email', 'Email')])
    conditions = models.ManyToManyField(ConditionType, blank=True)
    other_conditions = models.CharField(max_length=255, null=True, blank=True)
    allergies = models.TextField(null=True, blank=True)                 # Allergens
    dietary_needs = models.TextField(null=True, blank=True)             # Dietary requirements (vegetarian, etc.?)
    has_pets = models.BooleanField(default=False)                       # Whether has pets
    pets_type = models.CharField(max_length=100, null=True, blank=True) # Pet type if any

    def __str__(self):
        return f"{self.user_profile.get_full_name} [{self.user_profile.user.email}]"

# Volunteer-specific information
class VolunteerProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    university_course = models.CharField(max_length=255, null=True, blank=True) # Which university and major (currently or previously attended)
    profession = models.CharField(max_length=255, null=True, blank=True)        # Profession
    is_for_credit = models.BooleanField(default=False)                          # Whether volunteering for credit (why?)
    skills = models.TextField(null=True, blank=True)                            # Skills
    interests = models.TextField(null=True, blank=True)                         # Interests
    pvg_level = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('verified', 'Verified'),
        ('processing', 'Processing'),
        ('pending', 'Pending'),
        ('do_not_have', 'I do not have a PVG yet'),
    ]) # PVG level
    pvg_file = models.FileField(upload_to='certificates/pvg/', null=True, blank=True)
    motivation = models.TextField(null=True, blank=True)              # Motivation for joining
    preferred_tasks = models.ManyToManyField(SupportType, blank=True) # Preferred task content
    is_scheduled = models.BooleanField(default=False)                 # Whether scheduled (for matching)
    available_days = models.JSONField(default=list, blank=True)       # Preferred dates
    available_start_time = models.TimeField(null=True, blank=True)    # Preferred time
    available_end_time = models.TimeField(null=True, blank=True)
    preferred_distance_km = models.PositiveIntegerField(default=10)   # Preferred distance
    accept_pets = models.BooleanField(default=True)                   # Whether can accept pets
    max_task_count = models.PositiveIntegerField(default=3)           # Maximum number of tasks can take
    assigned_tasks_count = models.PositiveIntegerField(default=0)     # Current number of assigned tasks
    
    def __str__(self):
        return f"{self.user_profile.get_full_name} [{self.user_profile.user.email}]"

class AdminProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    area_to_focus = models.CharField(max_length=255, null=True, blank=True)
    project_goal = models.TextField(null=True, blank=True)
    expected_hours = models.CharField(max_length=255, null=True, blank=True)
    supervisor_contact = models.CharField(max_length=255, null=True, blank=True)
    consent_data_use = models.BooleanField(default=False)
    agreement_ethics = models.BooleanField(default=False)