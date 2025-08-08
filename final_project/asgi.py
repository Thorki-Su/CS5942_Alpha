import os
import logging
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')

logger = logging.getLogger(__name__)

# Lazy import websocket routes, ensure returning list
def get_websocket_urlpatterns():
    try:
        from communication.routing import get_websocket_urlpatterns as comm_get_patterns
        return comm_get_patterns()  # Assume routing.py's get_websocket_urlpatterns returns list
    except ImportError as e:
        logger.error(f"Error loading websocket_urlpatterns: {e}")
        raise

# Main ASGI application
base_application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(  # New: Security validation
        AuthMiddlewareStack(
            URLRouter(get_websocket_urlpatterns())  # URLRouter wraps list
        )
    ),
})

# Wrap with logged error handling
async def application(scope, receive, send):
    try:
        await base_application(scope, receive, send)
    except Exception as e:
        logger.error(f"[ASGI ERROR] Scope: {scope.get('type')} - {e}", exc_info=True)
        if scope['type'] == 'websocket':
            await send({'type': 'websocket.close', 'code': 1011})  # Close WS connection
        raise