from django import forms
from .models import Donation


class DonationForm(forms.ModelForm):
    AMOUNT_CHOICES = [
        ('10', '£10'),
        ('25', '£25'),
        ('50', '£50'),
        ('100', '£100'),
        ('custom', 'Custom Amount'),
    ]
    
    amount_choice = forms.ChoiceField(
        choices=AMOUNT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=False,
        label='Select Amount'
    )
    
    custom_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=1,
        max_value=10000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter custom amount',
            'step': '0.01'
        }),
        label='Custom Amount (£)'
    )
    
    class Meta:
        model = Donation
        fields = ['donor_name', 'donor_email', 'message', 'is_anonymous']
        widgets = {
            'donor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'donor_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Leave a message of support (optional)'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'donor_name': 'Full Name',
            'donor_email': 'Email Address',
            'message': 'Message (Optional)',
            'is_anonymous': 'Make this donation anonymous'
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill fields for authenticated users
        if user and user.is_authenticated:
            try:
                self.fields['donor_name'].initial = user.userprofile.get_full_name
                self.fields['donor_email'].initial = user.email
            except:
                self.fields['donor_email'].initial = user.email
    
    def clean(self):
        cleaned_data = super().clean()
        amount_choice = cleaned_data.get('amount_choice')
        custom_amount = cleaned_data.get('custom_amount')
        
        # Validate amount selection
        if amount_choice == 'custom':
            if not custom_amount:
                raise forms.ValidationError('Please enter a custom amount.')
            cleaned_data['amount'] = custom_amount
        elif amount_choice:
            cleaned_data['amount'] = float(amount_choice)
        else:
            raise forms.ValidationError('Please select a donation amount.')
        
        # Validate donor information
        if not cleaned_data.get('donor_name'):
            raise forms.ValidationError('Please enter your name.')
        
        if not cleaned_data.get('donor_email'):
            raise forms.ValidationError('Please enter your email address.')
        
        return cleaned_data