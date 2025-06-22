from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile, ClientProfile, CertificationType, ConditionType, VolunteerProfile, SupportType

true_and_false = [
    (True, 'Yes'),
    (False, 'No'),
]

#Client注册表
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
        queryset=CertificationType.objects.all(), #从CertificationType选取所有对象作为可选项
        widget=forms.CheckboxSelectMultiple, #复选框
        label='Certifications'
    )
    consent_safeguard = forms.BooleanField(
        label='I agree with the agreement',
        required=True,
        error_messages={'required':'You must agree with the agreement to continue.'}
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2') #可以加别的属性来控制顺序（不知道行不行）

    def save(self, commit=True):
        user = super().save(commit=False)
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

#Client在个人信息页面用于补充信息的表
class ClientProfileForm(forms.ModelForm):
    # profile_photo = forms.FileField(
    #     required=False,
    #     label='Please upload your photo',
    # )
    #尝试把图片摘出去
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
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('Female', 'female')], label='Gender')
    has_pets = forms.BooleanField(required=False, label='Do you have pets?')
    pets_type = forms.CharField(max_length=255, required=False, label='Pets Type')
    emergency_contact = forms.CharField(max_length=255)

    # 动态添加证书上传字段
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 获取 instance 的 certifications
        #certifications = []
        cert_names = []
        #if self.instance and self.instance.certifications:
        if self.instance and self.instance.certifications.exists():
            #certifications = self.instance.certifications
            cert_names = list(self.instance.certifications.values_list('name', flat=True))
        
        if 'PIP' in cert_names:
            self.fields['pip_certificate'] = forms.FileField(
                required=False,
                label='PIP Certificate',
                initial=self.instance.pip_certificate if self.instance else None
            )
        if 'ADP' in cert_names:
            self.fields['adp_certificate'] = forms.FileField(
                required=False,
                label='ADP Certificate',
                initial=self.instance.adp_certificate if self.instance else None
            )
        if 'LWC' in cert_names:
            self.fields['lwc_certificate'] = forms.FileField(
                required=False,
                label='LWC Certificate',
                initial=self.instance.lwc_certificate if self.instance else None
            )
        
        # if 'pip' in certifications:
        #     self.fields['pip_certificate'] = forms.FileField(required=False, label='PIP Certificate')
        # if 'adp' in certifications:
        #     self.fields['adp_certificate'] = forms.FileField(required=False, label='ADP Certificate')
        # if 'lwc' in certifications:
        #     self.fields['lwc_certificate'] = forms.FileField(required=False, label='LWC Certificate')

    class Meta:
        model = ClientProfile
        fields = [
            'conditions',
            'support_areas',
            'preferred_times',
            'allergies',
            'has_pets',
            'pets_type',
            'dietary_needs',
            'other_conditions',
            'other_support',
        ]
        widgets = {
            'preferred_times': forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g. {"Monday": ["09:00-11:00"], "Friday": ["14:00-16:00"]}'}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
            'dietary_needs': forms.Textarea(attrs={'rows': 2}),
        }


#Volunteer注册表
class VolunteerRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label='First Name')
    last_name = forms.CharField(max_length=100, label='Last Name')
    phone_number = forms.CharField(max_length=20, label='Phone Number')
    location = forms.CharField(max_length=255, label='Location/Postcode')
    university_course = forms.CharField(max_length=255, label='University and Course')
    profession = forms.CharField(max_length=255, label='Profession')
    #is_for_credit = forms.BooleanField(label='Are you volunteering for credit?', required=True)
    is_for_credit = forms.ChoiceField(
        label='Are you volunteering for credit?',
        choices=true_and_false,
        widget=forms.RadioSelect,
        required=True,
    )
    consent_safeguard = forms.BooleanField(
        label='I agree with the agreement',
        required=True,
        error_messages={'required':'You must agree with the agreement to continue.'}
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
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
                is_for_credit = self.cleaned_data['is_for_credit']
            )
        return user
    
class VolunteerProfileForm(forms.ModelForm):
    # profile_photo = forms.FileField(
    #     required=False,
    #     label='Please upload your photo',
    # )
    age = forms.ChoiceField(choices=[('18-24', '18-24'), ('25-54', '25-54'), ('55+', '55+')], label='Age')
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('Female', 'female')], label='Gender')
    emergency_contact = forms.CharField(max_length=255)
    preferred_tasks = forms.ModelMultipleChoiceField(
        queryset=SupportType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Preferred Tasks'
    )
    class Meta:
        model = VolunteerProfile
        fields = [
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

class ProfilePhotoForm(forms.ModelForm):
    profile_photo = forms.FileField(
        required=False,
        label='Please upload your photo',
    )
    class Meta:
        model = UserProfile
        fields = ['profile_photo']