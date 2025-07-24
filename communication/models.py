from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)  # 允许null用于群组
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey('task.Task', on_delete=models.CASCADE, null=True, blank=True)
    is_group = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.email} to {self.receiver.email if self.receiver else 'group'}: {self.content[:20]}"

class VideoCallSession(models.Model):
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_calls')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participated_calls', null=True, blank=True)
    task = models.ForeignKey('task.Task', on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.initiator.email} with {self.participant.email if self.participant else 'group'}"

class OneToOneChatSession(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions_as_user2')
    room_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user1.email} - {self.user2.email} ({self.room_name})"

    class Meta:
        unique_together = ('user1', 'user2')  # 确保唯一性
        constraints = [
            models.CheckConstraint(check=models.Q(user1__lt=models.F('user2')), name='user1_less_than_user2')
        ]  # 强制 user1.id < user2.id