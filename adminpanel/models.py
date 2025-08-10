from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
User = get_user_model()

class OperationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)  # Brief description of operation content
    timestamp = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False) # Convenient for categorized viewing

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"