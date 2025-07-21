from django.urls import path
from . import views

urlpatterns = [
    path('shift/', views.shift, name='shift'),
]