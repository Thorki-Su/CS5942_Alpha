from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('donate/', views.donation_page, name='donation_page'),
    path('donate/success/<int:donation_id>/', views.donation_success, name='donation_success'),
    path('donate/cancel/', views.donation_cancel, name='donation_cancel'),
    path('donations/', views.donation_list, name='donation_list'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]