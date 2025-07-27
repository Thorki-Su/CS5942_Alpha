from django import forms
from user.models import VolunteerProfile, SupportType

DAYS_OF_WEEK = [
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
]

class VolunteerAvailabilityForm(forms.ModelForm):
    available_days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = VolunteerProfile
        fields = [
            'is_scheduled',
            'available_days',
            'available_start_time',
            'available_end_time',
            'preferred_tasks',
            'preferred_distance_km',
            'accept_pets',
            'max_task_count',
        ]
        widgets = {
            'available_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'available_end_time': forms.TimeInput(attrs={'type': 'time'}),
            'preferred_tasks': forms.CheckboxSelectMultiple,
        }