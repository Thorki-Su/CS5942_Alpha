from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile, ClientProfile, CertificationType, ConditionType, VolunteerProfile, SupportType

true_and_false = [
    (True, 'Yes'),
    (False, 'No'),
]

class ClientRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label='First Name')
    last_name = forms.CharField(max_length=100, label='Last Name')
    phone_number = forms.CharField(max_length=20, label='Phone Number')
    contact_method = forms.ChoiceField(
        choices=[('email', 'Email'), ('phone', 'Phone')],
        label='Preferred Contact Method'
    )
    location = forms.CharField(max_length=255, label='Location/Postcode')
    certifications = forms.ModelMultipleChoiceField(
        queryset=CertificationType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Certifications'
    )
    consent_safeguard = forms.BooleanField(
        label='I agree with the agreement',
        required=True,
        error_messages={'required': 'You must agree with the agreement to continue.'}
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False # 禁用账户，直到点击激活链接
        user.role = 'client'
        user.username = self.cleaned_data['email']
        if commit:
            user.save()

            user_profile = UserProfile.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone_number=self.cleaned_data['phone_number'],
                location=self.cleaned_data['location'],
                consent_safeguard=True
            )
            client_profile = ClientProfile.objects.create(
                user_profile=user_profile,
                preferred_contact_method=self.cleaned_data['contact_method'],
            )
            client_profile.certifications.set(self.cleaned_data['certifications'])
        return user

class ClientProfileForm(forms.ModelForm):
    pip_certificate = forms.FileField(required=False, label='PIP Certificate')
    adp_certificate = forms.FileField(required=False, label='ADP Certificate')
    lwc_certificate = forms.FileField(required=False, label='LWC Certificate')
    nhs_certificate = forms.FileField(required=False, label='NHS Certificate')
    diagnosis = forms.FileField(required=False, label='Diagnosis from a Doctor')
    first_name = forms.CharField(max_length=100, label='First Name')
    last_name = forms.CharField(max_length=100, label='Last Name')
    phone_number = forms.CharField(max_length=20, label='Phone Number')
    location = forms.CharField(max_length=255, label='Location / Postcode')
    support_areas = forms.ModelMultipleChoiceField(
        queryset=SupportType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Support Areas'
    )
    conditions = forms.ModelMultipleChoiceField(
        queryset=ConditionType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Conditions you live with'
    )
    age = forms.ChoiceField(choices=[('18-24', '18-24'), ('25-54', '25-54'), ('55+', '55+')], label='Age')
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], label='Gender')
    has_pets = forms.BooleanField(required=False, label='Do you have pets?')
    pets_type = forms.CharField(max_length=255, required=False, label='Pets Type')
    emergency_contact = forms.CharField(max_length=255)

    class Meta:
        model = ClientProfile
        fields = [
            'conditions', 'support_areas', 'preferred_times', 'allergies',
            'has_pets', 'pets_type', 'dietary_needs', 'other_conditions',
            'other_support', 'pip_certificate', 'adp_certificate',
            'lwc_certificate', 'nhs_certificate', 'diagnosis'
        ]
        widgets = {
            'preferred_times': forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g. {"Monday": ["09:00-11:00"], "Friday": ["14:00-16:00"]}'}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
            'dietary_needs': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            user_profile = self.instance.user_profile
            self.fields['first_name'].initial = user_profile.first_name
            self.fields['last_name'].initial = user_profile.last_name
            self.fields['age'].initial = user_profile.age
            self.fields['gender'].initial = user_profile.gender
            self.fields['phone_number'].initial = user_profile.phone_number
            self.fields['location'].initial = user_profile.location
            self.fields['emergency_contact'].initial = user_profile.emergency_contact
        
        # 只在认证存在时才显示这些字段
            cert_names = list(self.instance.certifications.values_list('name', flat=True))
            for cert in ['PIP', 'ADP', 'LWC', 'NHS', 'Diagnosis']:
                field_key = cert.lower() + '_certificate' if cert != 'Diagnosis' else 'diagnosis'
                if cert not in cert_names:
                    self.fields.pop(field_key, None)

        # if self.instance and self.instance.certifications.exists():
        #     cert_names = list(self.instance.certifications.values_list('name', flat=True))
        #     if 'PIP' in cert_names:
        #         self.fields['pip_certificate'] = forms.FileField(
        #             required=False,
        #             label='PIP Certificate',
        #             initial=self.instance.pip_certificate if self.instance else None
        #         )
        #     if 'ADP' in cert_names:
        #         self.fields['adp_certificate'] = forms.FileField(
        #             required=False,
        #             label='ADP Certificate',
        #             initial=self.instance.adp_certificate if self.instance else None
        #         )
        #     if 'LWC' in cert_names:
        #         self.fields['lwc_certificate'] = forms.FileField(
        #             required=False,
        #             label='LWC Certificate',
        #             initial=self.instance.lwc_certificate if self.instance else None
        #         )
        #     if 'NHS' in cert_names:
        #         self.fields['nhs_certificate'] = forms.FileField(
        #             required=False,
        #             label='NHS Certificate',
        #             initial=self.instance.nhs_certificate if self.instance else None
        #         )
        #     if 'Diagnosis' in cert_names:
        #         self.fields['diagnosis'] = forms.FileField(
        #             required=False,
        #             label='Diagnosis from a Doctor',
        #             initial=self.instance.diagnosis if self.instance else None
        #         )

    def save(self, commit=True):
        instance = super().save(commit=False)
        user_profile = instance.user_profile
        user_profile.first_name = self.cleaned_data['first_name']
        user_profile.last_name = self.cleaned_data['last_name']
        user_profile.age = self.cleaned_data['age']
        user_profile.gender = self.cleaned_data['gender']
        user_profile.phone_number = self.cleaned_data['phone_number']
        user_profile.location = self.cleaned_data['location']
        user_profile.emergency_contact = self.cleaned_data['emergency_contact']
        user_profile.save()
        if commit:
            instance.save()
            # 保存上传的文件
            for field in ['pip_certificate', 'adp_certificate', 'lwc_certificate', 'nhs_certificate', 'diagnosis']:
                if field in self.cleaned_data:
                    file = self.cleaned_data.get(field)
                    if file and hasattr(file, 'name'):
                        setattr(instance, field, file)
            # for field_name, field_value in self.cleaned_data.items():
            #     if field_name in ['pip_certificate', 'adp_certificate', 'lwc_certificate', 'nhs_certificate', 'diagnosis']:
            #         setattr(instance, field_name, field_value)
            instance.save()
            self.save_m2m()
        return instance

class VolunteerRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label='First Name')
    last_name = forms.CharField(max_length=100, label='Last Name')
    phone_number = forms.CharField(max_length=20, label='Phone Number')
    location = forms.CharField(max_length=255, label='Location/Postcode')
    university_course = forms.CharField(max_length=255, label='University and Course')
    profession = forms.CharField(max_length=255, label='Profession')
    is_for_credit = forms.ChoiceField(
        label='Are you volunteering for credit?',
        choices=true_and_false,
        widget=forms.RadioSelect,
        required=True,
    )
    consent_safeguard = forms.BooleanField(
        label='I agree with the agreement',
        required=True,
        error_messages={'required': 'You must agree with the agreement to continue.'}
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False # 禁用账户，直到点击激活链接
        user.role = 'volunteer'
        user.username = self.cleaned_data['email']
        if commit:
            user.save()

            user_profile = UserProfile.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone_number=self.cleaned_data['phone_number'],
                location=self.cleaned_data['location'],
                consent_safeguard=True
            )
            volunteer_profile = VolunteerProfile.objects.create(
                user_profile=user_profile,
                university_course=self.cleaned_data['university_course'],
                profession=self.cleaned_data['profession'],
                is_for_credit=self.cleaned_data['is_for_credit']
            )
        return user
    
class VolunteerProfileForm(forms.ModelForm):
    first_name = forms.CharField(disabled=True, required=False, label='First Name')
    last_name = forms.CharField(disabled=True, required=False, label='Last Name')
    location = forms.CharField(disabled=True, required=False, label='Postcode')
    phone_number = forms.CharField(disabled=True, required=False, label='Phone Number')
    age = forms.ChoiceField(choices=[('18-24', '18-24'), ('25-54', '25-54'), ('55+', '55+')], label='Age')
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], label='Gender')
    emergency_contact = forms.CharField(max_length=255)
    preferred_tasks = forms.ModelMultipleChoiceField(
        queryset=SupportType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Preferred Tasks'
    )
    class Meta:
        model = VolunteerProfile
        fields = [
            'first_name',
            'last_name',
            'location',
            'phone_number',
            'skills',
            'interests',
            'preferred_tasks',
            'pvg_level',
            'pvg_file',
            'availability',
            'motivation'
        ]
        widgets = {
            'availability': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'e.g. {"Monday": ["09:00-11:00"], "Friday": ["14:00-16:00"]}'
            }),
            'motivation': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            user_profile = self.instance.user_profile
            self.fields['first_name'].initial = user_profile.first_name
            self.fields['last_name'].initial = user_profile.last_name
            self.fields['location'].initial = user_profile.location
            self.fields['phone_number'].initial = user_profile.phone_number
            self.fields['age'].initial = user_profile.age
            self.fields['gender'].initial = user_profile.gender
            self.fields['emergency_contact'].initial = user_profile.emergency_contact

    def save(self, commit=True):
        instance = super().save(commit=False)
        user_profile = instance.user_profile

        user_profile.first_name = self.cleaned_data['first_name']
        user_profile.last_name = self.cleaned_data['last_name']
        user_profile.location = self.cleaned_data['location']
        user_profile.phone_number = self.cleaned_data['phone_number']
        user_profile.age = self.cleaned_data['age']
        user_profile.gender = self.cleaned_data['gender']
        user_profile.emergency_contact = self.cleaned_data['emergency_contact']
        user_profile.save()

        if commit:
            instance.save()
            self.save_m2m()
        return instance

class ProfilePhotoForm(forms.ModelForm):
    profile_photo = forms.FileField(
        required=False,
        label='Please upload your photo',
    )
    class Meta:
        model = UserProfile
        fields = ['profile_photo']