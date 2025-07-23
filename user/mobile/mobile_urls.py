from django.urls import path
from . import mobile_views

urlpatterns = [
    # PATH BELOW REGISTERED FOR MOBILE
    path('login/token/', mobile_views.mobile_token_login, name='mobile_token_login'),
    path('register/client/', mobile_views.mobile_client_register, name='mobile_client_register'),
    path('register/volunteer/', mobile_views.mobile_volunteer_register, name='mobile_volunteer_register'),
    path('change_password/', mobile_views.change_password, name='change_password'),
    path('profile/', mobile_views.mobile_profile_view, name='mobile_profile'),
    path('edit/client/', mobile_views.mobile_client_profile_edit, name='edit_client_profile'),
    path('upload_avatar/', mobile_views.mobile_upload_avatar, name='mobile_upload_avatar'),
    path('save_preferred_times/', mobile_views.mobile_save_preferred_times, name='mobile_save_preferred_times'),
    path('edit/volunteer/', mobile_views.mobile_volunteer_profile_edit, name='edit_volunteer_profile'),

]