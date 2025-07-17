from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/choose/', views.choose_role, name='choose_role'),
    path('register/client/', views.client_register, name='client_register'),
    path('register/volunteer/', views.volunteer_register, name='volunteer_register'),
    path('client/profile/edit', views.client_profile_edit, name='client_profile_edit'),
    path('volunteer/profile/edit', views.volunteer_profile_edit, name='volunteer_profile_edit'),
    path('profile/', views.profile_detail, name='profile_detail'),
    path('profile/photoedit/', views.photo_edit, name='photo_edit'),
    path('save-preferred-times/', views.save_preferred_times, name='save_preferred_times'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
]