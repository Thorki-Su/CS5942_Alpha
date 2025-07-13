from django.contrib import admin
from .models import ChatMessage, VideoCallSession

admin.site.register(ChatMessage)
admin.site.register(VideoCallSession)