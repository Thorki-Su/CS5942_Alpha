from django.urls import re_path, path
from channels.routing import URLRouter
from . import views

def get_websocket_urlpatterns():
    from .consumers import ChatConsumer, VideoCallConsumer
    return [
        re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
        re_path(r'ws/video/(?P<room_name>\w+)/$', VideoCallConsumer.as_asgi()),
        re_path(r'ws/user/(?P<user_email>[\w.@+-]+)/$', ChatConsumer.as_asgi()),  # 修改正则表达式，允许 @ 和 .
    ]

websocket_urlpatterns = URLRouter(get_websocket_urlpatterns())

urlpatterns = [
    path('', views.message_selection_view, name='message_selection'),
    path('one-to-one-selection/', views.one_to_one_chat_selection_view, name='one_to_one_chat_selection'),
    path('task/<int:task_id>/chat/', views.task_communication_view, name='task_communication_view'),
    path('create-1v1-room/', views.create_one_to_one_room, name='create_one_to_one_room'),
    path('group-chats/', views.group_chats_view, name='group_chats'),
    path('one-to-one/<str:room_name>/', views.one_to_one_communication_view, name='one_to_one_communication_view'),
    path('unread-details/', views.get_unread_details, name='get_unread_details'),
]