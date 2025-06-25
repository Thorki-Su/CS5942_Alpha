from django.db import models
from user.models import CustomUser

class ChatMessage(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.email} to {self.receiver.email}: {self.content[:20]}"

class VideoCallSession(models.Model):
    initiator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='initiated_calls')
    participant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='participated_calls')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.initiator.email} with {self.participant.email}"