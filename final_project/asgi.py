import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_project.settings')
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from communication.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': URLRouter(websocket_urlpatterns),
})