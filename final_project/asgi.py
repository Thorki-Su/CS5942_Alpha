import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')

# 延迟导入，防止应用未加载
def get_websocket_urlpatterns():
    from communication.urls import get_websocket_urlpatterns
    return get_websocket_urlpatterns()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(get_websocket_urlpatterns())
    ),
})