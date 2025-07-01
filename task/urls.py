from django.urls import path
from . import views

urlpatterns = [
    path('task/mine/', views.mytask, name='mytask'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/detail/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/detail/<int:task_id>/applications/', views.task_application, name='task_application'),
    path('task/myapplication/', views.myapplication, name='myapplication'),
    path('task/available/', views.tasklist, name='tasklist'),
    path('task/ongoing/', views.task_ongoing, name='task_ongoing'),
]