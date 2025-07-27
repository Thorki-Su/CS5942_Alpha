from django.urls import path
from . import mobile_views

urlpatterns = [
    path('create/', mobile_views.mobile_create_task, name='mobile_create_task'),
    path('work-areas/', mobile_views.get_mobile_work_areas, name='mobile_work_areas'),
    path('my-tasks/', mobile_views.mobile_my_tasks, name='mobile_my_tasks'),
    path('list/', mobile_views.mobile_available_tasks, name='mobile_available_tasks'),
    path('volunteer/applications/', mobile_views.mobile_volunteer_applications, name='mobile_volunteer_applications'),
    path('volunteer/applications/<int:application_id>/cancel/', mobile_views.mobile_cancel_application, name='mobile_cancel_application'),
    path('volunteer/feedback/<int:task_id>/', mobile_views.mobile_volunteer_feedback, name='mobile_volunteer_feedback'),
    path('<int:task_id>/', mobile_views.mobile_task_detail, name='mobile_task_detail'),
    path('<int:task_id>/client/feedback/<int:volunteer_id>/', mobile_views.mobile_client_feedback, name='mobile_client_feedback'),
    path('<int:task_id>/applications/', mobile_views.mobile_task_applications, name='mobile_task_applications'),
    path('<int:task_id>/applications/<int:application_id>/approve/', mobile_views.mobile_approve_application, name='mobile_approve_application'),
    path('<int:task_id>/applications/<int:application_id>/reject/', mobile_views.mobile_reject_application, name='mobile_reject_application'),
    path('<int:task_id>/cancel/', mobile_views.mobile_cancel_task, name='mobile_cancel_task'),
    path('<int:task_id>/apply/', mobile_views.mobile_apply_for_task, name='mobile_apply_for_task'),
    path('<int:task_id>/force-complete/', mobile_views.force_complete_task, name='force_complete_task'),
    path('<int:task_id>/submit-record/', mobile_views.mobile_submit_task_record,name='mobile_submit_task_record'),
    path('<int:task_id>/record/', mobile_views.mobile_get_task_record, name='mobile_get_task_record'),
    path('<int:task_id>/confirm/', mobile_views.mobile_confirm_task, name='mobile_confirm_task'),
    
]
