from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
]

