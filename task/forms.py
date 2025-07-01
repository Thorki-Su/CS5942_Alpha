from django import forms
from .models import Task
from user.models import SupportType

class TaskForm(forms.ModelForm):
    work_area = forms.ModelMultipleChoiceField(
        queryset=SupportType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Needed Work Areas'
    )
    class Meta:
        model = Task
        fields = ['title', 'description', 'start_time', 'end_time', 'vol_number', 'work_area']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }