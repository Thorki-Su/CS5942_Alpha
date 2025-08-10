from django.urls import re_path
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

def get_websocket_urlpatterns():
    from .consumers import ChatConsumer  # Only import ChatConsumer (video/audio signaling merged)
    return [
        re_path(r'ws/chat/(?P<room_name>[\w.@+-]+)/$', ChatConsumer.as_asgi()),  # Unified path handling for chat/video/audio
        re_path(r'ws/user/(?P<user_email>[\w.@+-]+)/$', ChatConsumer.as_asgi()),
    ]

websocket_urlpatterns = URLRouter(get_websocket_urlpatterns())