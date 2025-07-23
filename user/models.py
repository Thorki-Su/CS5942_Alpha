from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from .utils import geocode_address

#用于自定义CustomUser（不使用username而是email
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
    is_active = models.BooleanField(default=False) #控制账户是否激活（考虑是否需要）
    is_staff = models.BooleanField(default=False) #控制账号访问管理后台的权限

    USERNAME_FIELD = 'email'                      #指定email为登录的标识（取代username）
    REQUIRED_FIELDS = []                          #创建用户时必须提供的字段

    objects = CustomUserManager()                 #将CustomUserManager绑定为此模型的管理器

    def __str__(self):
        return self.email
    
    def whether_in_task(self, task_id):           #判断这个用户有没有在指定任务中
        from task.models import Task, TaskApplication
        if self.role == 'client':
            return Task.objects.filter(client=self, id=task_id).exists()
        elif self.role == 'volunteer':
            return TaskApplication.objects.filter(volunteer=self, task_id=task_id, status='accepted').exists()
        return False

def user_directory_path(instance, filename):
    return f'profile_photos/{instance.user.email}/{filename}'

#用来储存不同用户之间都有的信息
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255)                                             #地理位置，或邮编
    location_lat = models.FloatField(null=True, blank=True)                                 #坐标，根据地理位置获得，无需自己填写
    location_lng = models.FloatField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to=user_directory_path, null=True, blank=True) #个人照片，用作头像和匹配时的展示
    emergency_contact = models.CharField(max_length=255, null=True, blank=True)             #紧急联系人（姓名+联系方式）
    eligibility_confirmed = models.BooleanField(default=False)                              #审核通过后改为True
    consent_safeguard = models.BooleanField(default=False)                                  #是否同意数据使用和安全协议（不确定是否有必要）

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
    def get_full_name(self): #获取全名
        return f"{self.first_name} {self.last_name}"

#储存福利认证的东西
class CertificationType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

#患病情况
class ConditionType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

#支持领域 
class SupportType(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

#储存Client独有的信息
class ClientProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    certifications = models.ManyToManyField(CertificationType)                               #是否有PIP、ADP、LWC等认证(多对多)
    pip_certificate = models.FileField(upload_to='certificates/pip/', null=True, blank=True) #如果有认证，客户需将之上传
    adp_certificate = models.FileField(upload_to='certificates/adp/', null=True, blank=True)
    lwc_certificate = models.FileField(upload_to='certificates/lwc/', null=True, blank=True)
    nhs_certificate = models.FileField(upload_to='certificates/nhs/', null=True, blank=True)
    diagnosis = models.FileField(upload_to='certificates/diagnosis/', null=True, blank=True)
    preferred_contact_method = models.CharField(max_length=20, choices=[('phone', 'Phone'), ('email', 'Email')])
    conditions = models.ManyToManyField(ConditionType, blank=True)
    other_conditions = models.CharField(max_length=255, null=True, blank=True)
    support_areas = models.ManyToManyField(SupportType, blank=True)
    other_support = models.CharField(max_length=255, null=True, blank=True)
    preferred_times = models.JSONField(default=dict, blank=True)        #需要帮助的时间，待考虑是否还需要
    allergies = models.TextField(null=True, blank=True)                 #过敏源
    dietary_needs = models.TextField(null=True, blank=True)             #饮食需求（素食之类的？）
    has_pets = models.BooleanField(default=False)                       #是否有宠物
    pets_type = models.CharField(max_length=100, null=True, blank=True) #有的话宠物类型

    def __str__(self):
        return f"{self.user_profile.get_full_name} [{self.user_profile.user.email}]"

#Volunteer独有的信息
class VolunteerProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    university_course = models.CharField(max_length=255, null=True, blank=True) #就读（曾就读）于哪所大学、专业
    profession = models.CharField(max_length=255, null=True, blank=True)        #职业
    is_for_credit = models.BooleanField(default=False)                          #是否为了学分而做志愿（为什么？）
    skills = models.TextField(null=True, blank=True)                            #技能
    interests = models.TextField(null=True, blank=True)                         #兴趣
    pvg_level = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('verified', 'Verified'),
        ('processing', 'Processing'),
        ('pending', 'Pending'),
        ('do_not_have', 'I do not have a PVG yet'),
    ]) #PVG等级
    pvg_file = models.FileField(upload_to='pvg/', null=True, blank=True)
    availability = models.JSONField(default=dict, blank=True)         #可以做志愿的时间，考虑是否还需要
    motivation = models.TextField(null=True, blank=True)              #加入的动机
    preferred_tasks = models.ManyToManyField(SupportType, blank=True) #意向任务内容
    is_scheduled = models.BooleanField(default=False)                 #是否排班（用于匹配）
    available_days = models.JSONField(default=list, blank=True)       #意向日期
    available_start_time = models.TimeField(null=True, blank=True)    #意向时间
    available_end_time = models.TimeField(null=True, blank=True)
    preferred_distance_km = models.PositiveIntegerField(default=10)   #意向距离
    accept_pets = models.BooleanField(default=True)                   #能否接受宠物
    
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

# 专供移动端使用的选项类型（不影响已有逻辑）
class TaskType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PVGLevelType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name