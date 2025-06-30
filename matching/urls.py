from django.urls import path
from .views import match_page, match_specific_volunteer, volunteer_list

urlpatterns = [
    path('match/', match_page, name='match_page'),
    path('volunteer-list/', volunteer_list, name='volunteer_list'),
    path('match-volunteer/<int:volunteer_id>/', match_specific_volunteer, name='match_specific_volunteer'),
]

