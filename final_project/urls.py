from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from channels.routing import URLRouter
from communication.urls import websocket_urlpatterns  # 导入 WebSocket 路由

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('user.urls', 'user'), namespace='user')),
    path('communication/', include(('communication.urls', 'communication'), namespace='communication')),
    path('', include(('task.urls', 'task'), namespace='task')),
    path('', include(('matching.urls', 'matching'), namespace='matching')),
]

# 确保 WebSocket 路由可访问
websocket_urlpatterns = websocket_urlpatterns  # 直接引用 communication.urls 中的定义

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # 可选：添加静态文件服务