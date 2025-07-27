from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('user.urls', 'user'), namespace='user')),
    path('communication/', include(('communication.urls', 'communication'), namespace='communication')),
    path('task/', include(('task.urls', 'task'), namespace='task')),
    path('matching', include(('matching.urls', 'matching'), namespace='matching')),
    path('adminpanel/', include(('adminpanel.urls', 'adminpanel'), namespace='adminpanel')),

    # paths below are all registered for mobile
    # path('api/mobile/', include('user.mobile.mobile_urls')),
    path('api/mobile/', include(('user.mobile.mobile_urls', 'mobile_user'), namespace='mobile_user')),
    path('mobile/task/', include(('task.mobile.mobile_urls', 'mobile_task'), namespace='mobile_task')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)