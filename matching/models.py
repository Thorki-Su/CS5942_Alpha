from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MatchRecord(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_matches')
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='volunteer_matches')
    client_email = models.EmailField()
    volunteer_email = models.EmailField()
    match_time = models.DateTimeField(auto_now_add=True)
    time_slot = models.CharField(max_length=100)  # 示例: "Sunday 14:00-17:00"
    meeting_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.client.email} <-> {self.volunteer.email} @ {self.match_time}"

