from django.urls import re_path, path
from channels.routing import URLRouter
from . import views

def get_websocket_urlpatterns():
    from .consumers import ChatConsumer, VideoCallConsumer
    return [
        re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
        re_path(r'ws/video/(?P<room_name>\w+)/$', VideoCallConsumer.as_asgi()),
    ]

websocket_urlpatterns = URLRouter(get_websocket_urlpatterns())  # 保持为 URLRouter 实例，但不直接在 asgi.py 使用

urlpatterns = [
    path('', views.message_selection_view, name='message_selection'),
    path('one-to-one-selection/', views.one_to_one_chat_selection_view, name='one_to_one_chat_selection'),
    path('task/<int:task_id>/chat/', views.task_communication_view, name='task_communication_view'),
    path('create-1v1-room/', views.create_one_to_one_room, name='create_one_to_one_room'),
    path('group-chats/', views.group_chats_view, name='group_chats'),
    path('one-to-one/<str:room_name>/', views.one_to_one_communication_view, name='one_to_one_communication_view'),
]