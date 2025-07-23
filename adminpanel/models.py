from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
User = get_user_model()

class OperationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)  # 简要描述操作内容
    timestamp = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False) # 方便分类查看

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"