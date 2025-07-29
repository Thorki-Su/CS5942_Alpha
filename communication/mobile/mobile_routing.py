# communication/mobile/mobile_routing.py

from .ws_paths import VIDEO_CALL_PATH
from django.urls import re_path

def get_websocket_urlpatterns():
    from communication.mobile.video_call_consumer import VideoCallConsumer  # ⏰ 延迟导入
    return [
        re_path(VIDEO_CALL_PATH, VideoCallConsumer.as_asgi()),
    ]

websocket_urlpatterns = get_websocket_urlpatterns()