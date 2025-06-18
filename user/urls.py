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
    path('client/profile/edit', views.client_profile_edit, name='client_profile_edit'),
    path('client/profile/view', views.client_profile_detail, name='client_profile_detail'),
]

