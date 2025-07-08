from django import forms
from .models import Task
from user.models import SupportType

class TaskForm(forms.ModelForm):
    vol_number = forms.IntegerField(min_value=1)
    work_area = forms.ModelMultipleChoiceField(
        queryset=SupportType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Needed Work Areas'
    )
    class Meta:
        model = Task
        fields = ['title', 'description', 'start_time', 'end_time', 'vol_number', 'work_area']
        widgets = {
            'start_time': forms.TextInput(attrs={'id': 'start_time'}),
            'end_time': forms.TextInput(attrs={'id': 'end_time'}),
        }

WEEKDAYS = [
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday'),
]

TIME_BLOCKS = [
    ('morning', '08:00–11:00'),
    ('midday', '11:00–14:00'),
    ('afternoon', '14:00–17:00'),
]

class TaskFilterForm(forms.Form):
    keyword = forms.CharField(required=False, label='Keyword', widget=forms.TextInput(attrs={'placeholder': 'Search title or description'}))
    weekday = forms.ChoiceField(choices=[('', 'Any day')] + WEEKDAYS, required=False)
    time_block = forms.ChoiceField(choices=[('', 'Any time')] + TIME_BLOCKS, required=False)
    work_area = forms.ModelChoiceField(queryset=SupportType.objects.all(), required=False, empty_label="All Areas")

class TaskRecordForm(forms.Form):
    record_0 = forms.CharField(label="Record 1", required=True)

    def get_record_list(self):
        return [value for key, value in self.cleaned_data.items() if key.startswith('record_')]