from django.db import models
from django.conf import settings
from user.models import CustomUser, UserProfile, ClientProfile, VolunteerProfile, SupportType
from django.utils import timezone

# Create your models here.
class Task(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open for application'),
        ('selected', 'Selecting Done'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    work_area = models.ManyToManyField(SupportType)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    vol_number = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posted_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.client.email})"
    
    def update_status_if_full(self):
        if self.status == 'cancelled':
            return
        approved_count = self.applications.filter(status='accepted').count()
        if approved_count >= self.vol_number and self.status != 'selected':
            self.status = 'selected'
            self.save()

    def update_status_by_time(self):
        """根据时间更新任务状态"""
        now = timezone.now()
        if self.status == 'cancelled':
            return
        if now > self.end_time:
            self.status = 'completed'
            self.closed_at = now
        elif now >= self.start_time and now <= self.end_time:
            self.status = 'ongoing'
        elif now < self.start_time and self.status != 'selected':
            self.status = 'open'
        self.save()
        
    def cancel(self):
        self.status = 'cancelled'
        self.closed_at = timezone.now()
        self.save()
        self.applications.update(status='cancelled')

    @property
    def is_active(self):
        return self.status in ['open', 'selected']
    
    @property
    def is_closed(self):
        return self.status in ['completed', 'cancelled']
    
    @property
    def is_ongoing(self):
        return self.status in ['ongoing']
    

class TaskApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('accepted', 'accepted'),
        ('unselected', 'unselected'),
        ('rejected', 'rejected'),
        ('cancelled', 'cancelled'),
    ]

    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='applications')
    volunteer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('task', 'volunteer')  # 每个志愿者只能申请一次

    def __str__(self):
        return f"{self.volunteer.email}applys for {self.task.title}"
    
    def cancel(self):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()
