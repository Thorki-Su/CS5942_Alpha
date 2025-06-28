from django.db import models
from user.models import CustomUser, UserProfile, ClientProfile, VolunteerProfile, SupportType

# Create your models here.
class Task(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open for application'),
        ('selected', 'Selecting Done'),
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
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posted_tasks')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.patient.email})"
    

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

    class Meta:
        unique_together = ('task', 'volunteer')  # 每个志愿者只能申请一次

    def __str__(self):
        return f"{self.volunteer.email}applys for {self.task.title}"
