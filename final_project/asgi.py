import os
import logging
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')
logger = logging.getLogger(__name__)

# 延迟导入，防止应用未加载
def get_websocket_urlpatterns():
    try:
        from communication.urls import get_websocket_urlpatterns
        return get_websocket_urlpatterns()
    except ImportError as e:
        logger.error(f"Error loading websocket_urlpatterns: {e}")
        raise

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(get_websocket_urlpatterns())
    ),
})

# 添加 WebSocket 连接错误处理
async def application_wrapper(scope, receive, send):
    try:
        await application(scope, receive, send)
    except Exception as e:
        logger.error(f"WebSocket application error: {e}")
        raise