from django.urls import re_path, path
from channels.routing import URLRouter
from . import views

def get_websocket_urlpatterns():
    from .consumers import ChatConsumer, VideoCallConsumer
    return [
        re_path(r'ws/chat/(?P<room_name>chat_\d+_\d+|chat_task_\d+)/$', ChatConsumer.as_asgi()),
        re_path(r'ws/video/(?P<room_name>chat_task_\d+)/$', VideoCallConsumer.as_asgi()),
    ]

websocket_urlpatterns = URLRouter(get_websocket_urlpatterns())

urlpatterns = [
    path('', views.communication_view, name='communication_view'),
    path('task/<int:task_id>/chat/', views.task_communication_view, name='task_communication_view'),
    path('group-chats/', views.group_chats, name='group_chats'),  # 新增组聊天室列表页面
]