from django import forms
from user.models import CustomUser

class AdminCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if commit:
            user.save()
        return user
