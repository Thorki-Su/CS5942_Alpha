from django.urls import re_path
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

def get_websocket_urlpatterns():
    from .consumers import ChatConsumer  # 只导入ChatConsumer（视频/音频信令已合并）
    return [
        re_path(r'ws/chat/(?P<room_name>[\w.@+-]+)/$', ChatConsumer.as_asgi()),  # 统一路径处理聊天/视频/音频
        re_path(r'ws/user/(?P<user_email>[\w.@+-]+)/$', ChatConsumer.as_asgi()),
    ]

websocket_urlpatterns = URLRouter(get_websocket_urlpatterns())