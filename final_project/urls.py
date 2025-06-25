from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('user.urls', 'user'), namespace='user')),
    path('communication/', include(('communication.urls', 'communication'), namespace='communication')),
    # path('', include('adminpanel.urls')), # 注释掉或移除，直到 adminpanel.urls 准备好
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)