from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),  
    # path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('dashboard/', views.dashboard_view, name='dashboard'),
    path('register/choose/', views.choose_role, name='choose_role'),
    path('register/client/', views.client_register, name='client_register'),
    path('register/volunteer/', views.volunteer_register, name='volunteer_register'),
    path('client/profile/edit', views.client_profile_edit, name='client_profile_edit'),
    path('volunteer/profile/edit', views.volunteer_profile_edit, name='volunteer_profile_edit'),
    path('profile/', views.profile_detail, name='profile_detail'),
    path('profile/photoedit/', views.photo_edit, name='photo_edit'),
]

