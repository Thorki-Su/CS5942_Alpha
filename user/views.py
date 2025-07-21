from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, UserProfile, ClientProfile, VolunteerProfile
from .forms import ClientRegisterForm, ClientProfileForm, VolunteerRegisterForm, VolunteerProfileForm, ProfilePhotoForm
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.forms.models import model_to_dict
from django.core.files.base import ContentFile
import base64
import re
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import json
from django.utils.safestring import mark_safe
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from task.models import Task
from user.utils import geocode_address, is_valid_aberdeen_postcode, send_activation_email
from volunteer.utils import calculate_volunteer_duration, format_volunteer_duration
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

def home_view(request):
    tasks = Task.objects.filter(client=request.user) if request.user.is_authenticated and request.user.role == 'client' else []
    return render(request, 'user/home.html', {'tasks': tasks})

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # 映射 email
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
      
            if user is not None:
                login(request, user)
                if user.role == 'admin':
                    return redirect('adminpanel:dashboard')
                return redirect('user:home')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid form data or CSRF token.")
            print(form.errors)  # 调试 CSRF 错误
    else:
        form = AuthenticationForm()
    return render(request, 'user/login.html', {'form': form})

def logout_view(request):
    list(messages.get_messages(request))
    logout(request)
    return redirect('user:login')

def choose_role(request):
    return render(request, 'user/role_choose.html')

def client_register(request):
    if request.method == 'POST':
        form = ClientRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            location = form.cleaned_data.get('location')
            if not is_valid_aberdeen_postcode(location):
                form.add_error('location', 'Please enter a valid postcode within Aberdeen')
            else:
                user = form.save()
                send_activation_email(user, request)
                return render(request, 'user/please_check_email.html')
        else:
            print(form.errors)
    else:
        form = ClientRegisterForm()
    return render(request, 'user/client_register.html', {'form': form})

def volunteer_register(request):
    if request.method == 'POST':
        form = VolunteerRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            location = form.cleaned_data.get('location')
            if not is_valid_aberdeen_postcode(location):
                form.add_error('location', 'Please enter a valid postcode within Aberdeen')
            else:
                user = form.save()
                send_activation_email(user, request)
                return render(request, 'user/please_check_email.html')
        else:
            print(form.errors)
    else:
        form = VolunteerRegisterForm()
    return render(request, 'user/volunteer_register.html', {'form': form})

def activate_account(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'user/activation_success.html')
    else:
        return render(request, 'user/activation_failed.html')

@login_required
def client_profile_edit(request):
    try:
        client_profile = request.user.userprofile.clientprofile
    except ClientProfile.DoesNotExist:
        return redirect('user:choose_role')
    
    if request.method == 'POST':
        form = ClientProfileForm(request.POST, request.FILES, instance=client_profile)
        if form.is_valid():
            form.save()
            return redirect('user:profile_detail')
        else:
            print(form.errors)
    else:
        form = ClientProfileForm(
            instance=client_profile,
            initial={
                'first_name': request.user.userprofile.first_name,
                'last_name': request.user.userprofile.last_name,
                'phone_number': request.user.userprofile.phone_number,
                'location': request.user.userprofile.location,
                'age': request.user.userprofile.age,
                'gender': request.user.userprofile.gender,
                'emergency_contact': request.user.userprofile.emergency_contact
            }
        )
    return render(request, 'user/client_profile_edit.html', {'form': form})

@login_required
def volunteer_profile_edit(request):
    try:
        volunteer_profile = request.user.userprofile.volunteerprofile
    except VolunteerProfile.DoesNotExist:
        return redirect('user:choose_role')
    if request.method == 'POST':
        form = VolunteerProfileForm(request.POST, request.FILES, instance=volunteer_profile)
        if form.is_valid():
            form.save()
            return redirect('user:profile_detail')
        else:
            print(form.errors)
    else:
        form = VolunteerProfileForm(
            instance=volunteer_profile,
            initial={
                'first_name': request.user.userprofile.first_name,
                'last_name': request.user.userprofile.last_name,
                'phone_number': request.user.userprofile.phone_number,
                'location': request.user.userprofile.location,
                'age': request.user.userprofile.age,
                'gender': request.user.userprofile.gender,
                'emergency_contact': request.user.userprofile.emergency_contact
            }
        )
    return render(request, 'user/volunteer_profile_edit.html', {'form': form})

@login_required
def profile_detail(request):
    user = request.user
    user_profile = user.userprofile
    user_fields = model_to_dict(user_profile)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    time_slots = ['08:00-11:00', '11:00-14:00', '14:00-17:00']

    if user.role == 'client':
        client_profile = user_profile.clientprofile
        client_fields = model_to_dict(client_profile)

        client_fields['certifications'] = ", ".join(
            [c.name for c in client_profile.certifications.all()]
        )
        client_fields['conditions'] = ", ".join(
            [c.name for c in client_profile.conditions.all()]
        )
        client_fields['support_areas'] = ", ".join(
            [s.name for s in client_profile.support_areas.all()]
        )
        cert_list = client_profile.certifications.all()
        has_pip_cert = any(c.name == 'PIP' for c in cert_list)
        has_adp_cert = any(c.name == 'ADP' for c in cert_list)
        has_lwc_cert = any(c.name == 'LWC' for c in cert_list)
        preferred_times = client_fields.get('preferred_times', {})
        if isinstance(preferred_times, str):
            try:
                preferred_times = json.loads(preferred_times)
            except json.JSONDecodeError:
                preferred_times = {}

        context = {
            'user': user,
            'user_profile': user_profile,
            'client_profile': client_profile,
            'user_fields': user_fields,
            'client_fields': client_fields,
            'has_pip_cert': has_pip_cert,
            'has_adp_cert': has_adp_cert,
            'has_lwc_cert': has_lwc_cert,
            'days': days,
            'time_slots': time_slots,
            'preferred_times': preferred_times,
        }
    elif user.role == 'volunteer':
        volunteer_profile = user_profile.volunteerprofile
        volunteer_fields = model_to_dict(volunteer_profile)
        preferred_times = volunteer_fields.get('availability', {})
        if isinstance(preferred_times, str):
            try:
                preferred_times = json.loads(preferred_times)
            except json.JSONDecodeError:
                preferred_times = {}

        # Calculate volunteer duration
        total_hours = calculate_volunteer_duration(user)
        formatted_duration = format_volunteer_duration(total_hours)

        context = {
            'user': user,
            'user_profile': user_profile,
            'volunteer_profile': volunteer_profile,
            'user_fields': user_fields,
            'volunteer_fields': volunteer_fields,
            'days': days,
            'time_slots': time_slots,
            'preferred_times': preferred_times,
            'volunteer_duration': formatted_duration,
            'volunteer_duration_hours': total_hours,
        }
    else:
        context = {
            'user': user,
            'user_profile': user_profile,
            'user_fields': user_fields,
            'days': days,
            'preferred_times': {},
        }
    return render(request, 'user/profile_detail.html', context)

@login_required
def photo_edit(request):
    try:
        user_profile = request.user.userprofile
    except Exception:
        return redirect('user:choose_role')
    
    s3_storage = S3Boto3Storage()
    
    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=user_profile)

        cropped_data = request.POST.get('cropped_image_data')
        if cropped_data:
            format, imgstr = cropped_data.split(';base64,')
            ext = format.split('/')[-1]
            img_data = ContentFile(base64.b64decode(imgstr), name=f'user_{request.user.id}_cropped.{ext}')
            filename = s3_storage.save(f'profile_photos/{request.user.email}/{img_data.name}', img_data)
            user_profile.profile_photo.name = filename
            user_profile.save()
            return redirect('user:profile_detail')
        elif form.is_valid():
            if 'profile_photo' in request.FILES:
                f = request.FILES['profile_photo']
                filename = s3_storage.save(f'profile_photos/{request.user.email}/{f.name}', f)
                user_profile.profile_photo.name = filename
                user_profile.save()
            else:
                form.save()
            return redirect('user:profile_detail')
        else:
            print(form.errors)
    else:
        form = ProfilePhotoForm(instance=user_profile)
    return render(request, 'user/photo_edit.html', {'form': form})

@login_required
@ensure_csrf_cookie
def save_preferred_times(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_profile = request.user.userprofile
        if request.user.role == 'client':
            client_profile = user_profile.clientprofile
            client_profile.preferred_times = data
            client_profile.save()
        elif request.user.role == 'volunteer':
            volunteer_profile = user_profile.volunteerprofile
            volunteer_profile.availability = data
            volunteer_profile.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'user/password_change.html'
    success_url = reverse_lazy('user:password_change_done')