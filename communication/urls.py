from django.urls import re_path, path
from channels.routing import URLRouter
from . import consumers  # Keep as is if consumers need lazy loading
from .views import task_history
from .views import (
    message_selection_view, one_to_one_chat_selection_view, task_communication_view,
    create_one_to_one_room, group_chats_view, one_to_one_communication_view,
    get_unread_details, get_recent_chats, friend_list, send_friend_request,
    accept_friend_request, reject_friend_request
)

# Lazy load consumers
def get_websocket_urlpatterns():
    from .consumers import ChatConsumer  # Only import ChatConsumer (video signaling merged)
    return [
        re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),  # Unified path handling for chat/video/audio
        re_path(r'ws/user/(?P<user_email>[\w.@+-]+)/$', ChatConsumer.as_asgi()),  # Modified regex to allow @ and .
    ]

websocket_urlpatterns = URLRouter(get_websocket_urlpatterns())

urlpatterns = [
    path('', message_selection_view, name='message_selection'),
    path('one-to-one-selection/', one_to_one_chat_selection_view, name='one_to_one_chat_selection'),
    path('task/<int:task_id>/chat/', task_communication_view, name='task_communication_view'),
    path('create-1v1-room/', create_one_to_one_room, name='create_one_to_one_room'),
    path('group-chats/', group_chats_view, name='group_chats'),
    path('one-to-one/<str:room_name>/', one_to_one_communication_view, name='one_to_one_communication_view'),
    path('unread-details/', get_unread_details, name='get_unread_details'),
    path('get-recent-chats/', get_recent_chats, name='get_recent_chats'),
    path('friends/', friend_list, name='friend_list'),
    path('send-friend-request/', send_friend_request, name='send_friend_request'),
    path('accept-friend-request/<int:request_id>/', accept_friend_request, name='accept_friend_request'),
    path('reject-friend-request/<int:request_id>/', reject_friend_request, name='reject_friend_request'),
    path('task/<int:task_id>/history/', task_history, name='task_history'),
]