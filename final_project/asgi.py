import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')

def get_asgi_application():
    django.setup()  # 确保应用注册完成
    from django.core.asgi import get_asgi_application
    from communication.urls import websocket_urlpatterns  # 使用 urls 中的 websocket_urlpatterns
    return ProtocolTypeRouter({
        'http': get_asgi_application(),
        'websocket': websocket_urlpatterns,
    })

application = get_asgi_application()