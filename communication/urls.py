from django.urls import re_path, path
from channels.routing import URLRouter
from . import views

# 延迟加载 consumers
def get_websocket_urlpatterns():
    from .consumers import ChatConsumer, VideoCallConsumer
    return [
        re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
        re_path(r'ws/video/(?P<room_name>\w+)/$', VideoCallConsumer.as_asgi()),
    ]

websocket_urlpatterns = URLRouter(get_websocket_urlpatterns())

urlpatterns = [
    path('', views.communication_view, name='communication_view'),
    path('start-video-call/', views.start_video_call, name='start_video_call'),
    path('task/<int:task_id>/chat/', views.task_communication_view, name='task_communication_view'),
]