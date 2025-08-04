import os
import logging
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')

logger = logging.getLogger(__name__)

# 延迟导入 websocket 路由，确保返回列表
def get_websocket_urlpatterns():
    try:
        from communication.routing import get_websocket_urlpatterns as comm_get_patterns
        return comm_get_patterns()  # 假设routing.py的get_websocket_urlpatterns返回列表
    except ImportError as e:
        logger.error(f"Error loading websocket_urlpatterns: {e}")
        raise

# 主 ASGI 应用
base_application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(  # 新增：安全验证
        AuthMiddlewareStack(
            URLRouter(get_websocket_urlpatterns())  # URLRouter包装列表
        )
    ),
})

# 包装带日志的错误处理
async def application(scope, receive, send):
    try:
        await base_application(scope, receive, send)
    except Exception as e:
        logger.error(f"[ASGI ERROR] Scope: {scope.get('type')} - {e}", exc_info=True)
        if scope['type'] == 'websocket':
            await send({'type': 'websocket.close', 'code': 1011})  # 关闭WS连接
        raise