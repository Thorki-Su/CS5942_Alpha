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
    path('volunteer/', include(('volunteer.urls', 'volunteer'), namespace='volunteer')),
    path('payment/', include(('payment.urls', 'payment'), namespace='payment')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)