from django.urls import path,include
from . import views

urlpatterns = [
    path('mine/', views.mytask, name='mytask'),
    path('create/', views.task_create, name='task_create'),
    path('detail/<int:task_id>/', views.task_detail, name='task_detail'),
    path('detail/<int:task_id>/applications/', views.task_application, name='task_application'),
    path('myapplication/', views.myapplication, name='myapplication'),
    path('available/', views.tasklist, name='tasklist'),
    path('ongoing/', views.task_ongoing, name='task_ongoing'),
    path('apply/<int:task_id>/', views.task_apply, name='task_apply'),
    path('application/<int:application_id>/approve/', views.approve_application, name='approve_application'),
    path('application/<int:application_id>/reject/', views.reject_application, name='reject_application'),
    path('cancel/<int:task_id>/', views.cancel_task, name='cancel_task'),
    path('cancel/applicaiton/<int:task_id>/', views.cancel_application, name='cancel_application'),
    path('<int:task_id>/confirm/', views.task_confirm, name='task_confirm'),
    path('<int:task_id>/record/', views.task_record, name='task_record'),
    path('<int:task_id>/feedback/<int:to_user_id>/', views.task_feedback, name='task_feedback'),
]