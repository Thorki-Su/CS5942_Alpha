from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

#用于自定义CustomUser（不使用username而是email）
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

#自定义用户
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)        #储存邮箱，唯一
    role = models.CharField(max_length=20, choices=[
        ('client', 'Client'),
        ('volunteer', 'Volunteer'),
        ('admin', 'Admin'),
    ])                                            #区分用户类型：客户、志愿者和管理员
    is_active = models.BooleanField(default=True) #控制账户是否激活（考虑是否需要）
    is_staff = models.BooleanField(default=False) #控制账号访问管理后台的权限

    USERNAME_FIELD = 'email'                      #指定email为登录的标识（取代username）
    REQUIRED_FIELDS = []                          #创建用户时必须提供的字段

    objects = CustomUserManager()                 #将CustomUserManager绑定为此模型的管理器

    def __str__(self):
        return self.email

def user_directory_path(instance, filename):
    return f'profile_photos/{instance.user.email}/{filename}'

#用来储存不同用户之间都有的信息
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)                     #和CustomUser一对一
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)                       #性别，需要考虑做成选择框还是填写
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255)                                           #地理位置，或邮编
    profile_photo = models.ImageField(upload_to=user_directory_path, null=True, blank=True) #个人照片，用作头像和匹配时的展示
    emergency_contact = models.CharField(max_length=255, null=True, blank=True)           #紧急联系人（姓名+联系方式）
    consent_safeguard = models.BooleanField(default=False)                                #是否同意数据使用和安全协议（不确定是否有必要）

#储存福利认证的东西
class CertificationType(models.Model):
    name = models.CharField(max_length=100) #存有例如PIP、ADP等名字
    def __str__(self):
        return self.name

#患病情况
class ConditionType(models.Model):
    name = models.CharField(max_length=100) #各种病（问Sarah）
    def __str__(self):
        return self.name

#支持领域    
class SupportType(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

#储存Client独有的信息
class ClientProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)             #和UserProfile一对一
    certifications = models.ManyToManyField(CertificationType)                             #是否有PIP、ADP、LWC等认证(多对多)
    pip_certificate = models.FileField(upload_to='certificates/pip/',null=True,blank=True) #如果有认证，客户需将之上传
    adp_certificate = models.FileField(upload_to='certificates/adp/',null=True,blank=True)
    lwc_certificate = models.FileField(upload_to='certificates/lwc/',null=True,blank=True)
    eligibility_confirmed = models.BooleanField(default=False)                             #审核通过后改为True
    preferred_contact_method = models.CharField(max_length=20, choices=[('phone', 'Phone'),('email', 'Email')])
    conditions = models.ManyToManyField(ConditionType, blank=True)                         #患病类型，多对多
    other_conditions = models.CharField(max_length=255, null=True, blank=True)
    support_areas = models.ManyToManyField(SupportType, blank=True)                #需要支持的领域（不确定要不要也做成多对多）
    other_support = models.CharField(max_length=255, null=True, blank=True)
    preferred_times = models.JSONField(default=dict, blank=True)                           #需要帮助的时间
    allergies = models.TextField(null=True, blank=True)                                    #过敏源
    dietary_needs = models.TextField(null=True, blank=True)                                #饮食需求（素食之类的？）
    has_pets = models.BooleanField(default=False)                                          #是否有宠物
    pets_type = models.CharField(max_length=100, null=True, blank=True)                    #有的话宠物类型

#Volunteer独有的信息
class VolunteerProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    university_course = models.CharField(max_length=255, null=True, blank=True) #就读（曾就读）于哪所大学、专业
    profession = models.CharField(max_length=255, null=True, blank=True) #职业
    is_for_credit = models.BooleanField(default=False)                   #是否为了学分而做志愿（为什么？）
    skills = models.TextField(null=True, blank=True)                     #技能
    interests = models.TextField(null=True, blank=True)                  #兴趣
    pvg_level = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('verified', 'Verified'),
        ('processing', 'Processing'),
        ('pending', 'Pending'),
        ('do_not_have', 'I do not have a PVG yet'),
    ])   #PVG等级
    pvg_file = models.FileField(upload_to='pvg/',null=True,blank=True)
    availability = models.JSONField(default=dict, blank=True)            #可以做志愿的时间
    motivation = models.TextField(null=True, blank=True)                 #加入的动机
    preferred_tasks = models.ManyToManyField(SupportType, blank=True)

#Admin独有的信息
class AdminProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    area_to_focus = models.CharField(max_length=255, null=True, blank=True)      #研究方向
    project_goal = models.TextField(null=True, blank=True)                       #项目目标
    expected_hours = models.CharField(max_length=255, null=True, blank=True)     #预计参与时间
    supervisor_contact = models.CharField(max_length=255, null=True, blank=True) #导师的联系方式
    consent_data_use = models.BooleanField(default=False)                        #是否同意使用匿名化客户数据
    agreement_ethics = models.BooleanField(default=False)                        #是否同意研究伦理与保密协议