from django.urls import path
from . import views

app_name = 'volunteer'

urlpatterns = [
    path('certificate/', views.service_certificate, name='service_certificate'),
    path('certificate/download/', views.download_certificate, name='download_certificate'),
    path('api/stats/', views.get_volunteer_stats, name='get_volunteer_stats'),
]