from django.urls import re_path
from communication.mobile import mobile_consumer

websocket_urlpatterns = [
    re_path(r'ws/mobile/video-call/(?P<room_name>\w+)/$', mobile_consumer.MobileVideoCallConsumer.as_asgi()),
]
