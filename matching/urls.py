from django.urls import path
from . import views

urlpatterns = [
    path('matching/shift/', views.shift, name='shift'),
]