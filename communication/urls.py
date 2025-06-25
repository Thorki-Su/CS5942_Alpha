from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('', views.communication_view, name='communication_view'),
    path('start-video-call/', views.start_video_call, name='start_video_call'),
]