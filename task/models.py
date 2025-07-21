from django.db import models
from django.conf import settings
from user.models import CustomUser, UserProfile, ClientProfile, VolunteerProfile, SupportType
from django.utils import timezone
from datetime import timedelta

class Task(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open for application'),
        ('selected', 'Selecting Done'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('timeout', 'Timeout'),
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
    confirmed_by_client = models.BooleanField(default=False)
    volunteer_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.client.email})"
    
    def update_status_if_full(self):
        if self.status == 'cancelled':
            return
        approved_count = self.applications.filter(status='accepted').count()
        if approved_count >= self.vol_number and self.status != 'selected':
            self.status = 'selected'
            self.save()
        elif self.status == 'selected' and approved_count < self.vol_number:
            self.status = 'open'
            self.save()

    def update_status_by_time(self):
        now = timezone.now()
        if self.status in ['cancelled', 'completed']:
            return
        approved_count = self.applications.filter(status='accepted').count()
        if now >= self.start_time and now <= self.end_time + timedelta(hours=2):
            if approved_count == 0:
                self.status = 'cancelled'
                self.closed_at = now
                for application in self.applications.all():
                    application.cancel()
            else:
                if self.status != 'ongoing':
                    self.status = 'ongoing'
                    self.applications.filter(status='pending').update(status='unselected')
        elif now > self.end_time + timedelta(hours=2):
            if approved_count == 0:
                self.status = 'cancel'
                self.closed_at = now
                for application in self.applications.all():
                    application.cancel()
            elif not self.confirmed_by_client:
                self.status = 'timeout'
            else:
                self.status = 'completed'
            for application in self.applications.all():
                application.complete()
            self.closed_at = now
        elif now < self.start_time and self.status not in ['selected', 'timeout']:
            self.status = 'open'
        self.save()
        
    def cancel(self):
        self.status = 'cancelled'
        self.closed_at = timezone.now()
        self.save()
        for application in self.applications.all():
            application.cancel()

    def is_within_24h(self):
        return self.start_time - timezone.now() < timedelta(hours=24)

    @property
    def is_active(self):
        return self.status in ['open', 'selected']
    
    @property
    def is_closed(self):
        return self.status in ['completed', 'cancelled']
    
    @property
    def is_ongoing(self):
        return self.status in ['ongoing', 'timeout']

class TaskApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('accepted', 'accepted'),
        ('unselected', 'unselected'),
        ('rejected', 'rejected'),
        ('cancelled', 'cancelled'),
        ('completed', 'completed'),
    ]

    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='applications')
    volunteer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    is_auto_matched = models.BooleanField(default=False)

    class Meta:
        unique_together = ('task', 'volunteer') # 每个志愿者只能申请一次

    def __str__(self):
        return f"{self.volunteer.email} applies for {self.task.title}"
    
    def cancel(self):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()
        self.task.update_status_if_full()

    def complete(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        self.task.update_status_if_full()

    def can_be_cancelled(self):
        return not self.task.is_within_24h()
    
    @property
    def is_active(self):
        return self.status in ['pending', 'accepted']
    
    @property
    def is_closed(self):
        return self.status in ['unselected', 'rejected', 'cancelled', 'completed']

class TaskTemplate(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField()
    work_area = models.ManyToManyField(SupportType)

    def __str__(self):
        return self.name

class TaskRecord(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='record')
    volunteer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    records = models.JSONField(default=list)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record for {self.task.title} by {self.volunteer.userprofile.get_full_name} [{self.volunteer.email}]"

class Feedback(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='feedbacks')
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feedbacks_given')
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feedbacks_received')
    is_satisfied = models.BooleanField()
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'from_user', 'to_user')

class StarRelation(models.Model):
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='starred_users')
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='starred_by')
    starred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')