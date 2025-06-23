from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, UserProfile, ClientProfile, VolunteerProfile
from .forms import ClientRegisterForm, ClientProfileForm, VolunteerRegisterForm, VolunteerProfileForm, ProfilePhotoForm
from django.contrib.auth.forms import AuthenticationForm
from django.forms.models import model_to_dict
from django.core.files.base import ContentFile
import base64
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.safestring import mark_safe

def home_view(request):
    return render(request, 'user/home.html')

# The view of register
# def register_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password1 = request.POST.get('password1')
#         password2 = request.POST.get('password2')

#         if password1 != password2:
#             messages.error(request, "The two passwords are inconsistent.")
#             return redirect('register')

#         if User.objects.filter(username=username).exists():
#             messages.error(request, "The user name already exists.")
#             return redirect('register')

#         user = User.objects.create_user(username=username, email=email, password=password1)
#         user.save()
#         messages.success(request, "Registration is successful, please log in.")
#         return redirect('login')

#     return render(request, 'user/register.html')


#  The view of login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('user:home')
        else:
            messages.error(request, "Wrong email or password.")
            return redirect('user:login')
    else:
        form = AuthenticationForm()
    return render(request, 'user/login.html', {'form':form})


# the view of log out
def logout_view(request):
    logout(request)
    return redirect('user:login')


# the view of page
# def dashboard_view(request):
#     if not request.user.is_authenticated:
#         return redirect('login')
#     return render(request, 'user/dashboard.html', {'user': request.user})

def choose_role(request):
    return render(request, 'user/role_choose.html')

def client_register(request):
    if request.method == 'POST':
        form = ClientRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('user:home')
        else: #展示错误，之后没问题了可以去掉
            print(form.errors)
    else:
        form = ClientRegisterForm()
    return render(request, 'user/client_register.html', {'form':form})

def volunteer_register(request):
    if request.method == 'POST':
        form = VolunteerRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('user:home')
        else: #同理
            print(form.errors)
    else:
        form = VolunteerRegisterForm()
    return render(request, 'user/volunteer_register.html', {'form':form})

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
            user_profile = request.user.userprofile
            # profile_photo_file = form.cleaned_data.get('profile_photo') 
            user_age = form.cleaned_data.get('age')#手动保存年龄和性别
            user_gender = form.cleaned_data.get('gender')
            user_emergency_contact = form.cleaned_data.get('emergency_contact')
            # if profile_photo_file:
            #     user_profile.profile_photo = profile_photo_file
            #     user_profile.save()
            
            if user_age:
                user_profile.age = user_age
                user_profile.save()

            if user_gender:
                user_profile.gender = user_gender
                user_profile.save()

            if user_emergency_contact:
                user_profile.emergency_contact = user_emergency_contact
                user_profile.save()

            return redirect('user:profile_detail')
        else: #同理
            print(form.errors)
    else:
        form = ClientProfileForm(
            instance=client_profile,
            initial={
                'age': request.user.userprofile.age,
                'gender': request.user.userprofile.gender,
                'emergency_contact': request.user.userprofile.emergency_contact
            }
        )
    return render(request, 'user/client_profile_edit.html', {'form':form})

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
            user_profile = request.user.userprofile
            # profile_photo_file = form.cleaned_data.get('profile_photo') 
            user_age = form.cleaned_data.get('age') #同理
            user_gender = form.cleaned_data.get('gender')
            user_emergency_contact = form.cleaned_data.get('emergency_contact')
            # if profile_photo_file:
            #     user_profile.profile_photo = profile_photo_file
            #     user_profile.save()
            
            if user_age:
                user_profile.age = user_age
                user_profile.save()

            if user_gender:
                user_profile.gender = user_gender
                user_profile.save()

            if user_emergency_contact:
                user_profile.emergency_contact = user_emergency_contact
                user_profile.save()
            
            return redirect('user:profile_detail')
        else: #同理
            print(form.errors)
    else:
        form = VolunteerProfileForm(
            instance=volunteer_profile,
            initial={
                'age': request.user.userprofile.age,
                'gender': request.user.userprofile.gender,
                'emergency_contact': request.user.userprofile.emergency_contact
            }
        )
    return render(request, 'user/volunteer_profile_edit.html', {'form':form})

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
        preferred_times = volunteer_fields.get('preferred_times', {})
        if isinstance(preferred_times, str):
            try:
                preferred_times = json.loads(preferred_times)
            except json.JSONDecodeError:
                preferred_times = {}
        context = {
            'user': user,
            'user_profile': user_profile,
            'volunteer_profile': volunteer_profile,
            'user_fields': user_fields,
            'volunteer_fields': volunteer_fields,
            'days': days,
            'time_slots': time_slots,
            'preferred_times': preferred_times,
        }
    return render(request, 'user/profile_detail.html', context)

@login_required
def photo_edit(request):
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('user:choose_role')
    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=user_profile)

        cropped_data = request.POST.get('cropped_image_data')
        if cropped_data:
            # 裁剪后的 base64 数据，转成图片
            format, imgstr = cropped_data.split(';base64,')
            ext = format.split('/')[-1]
            img_data = ContentFile(base64.b64decode(imgstr), name=f'user_{request.user.id}_cropped.{ext}')
            user_profile.profile_photo = img_data
            user_profile.save()
            return redirect('user:profile_detail')
        elif form.is_valid():
            form.save()
            return redirect('user:profile_detail')
        else:
            print(form.errors)
    else:
        form = ProfilePhotoForm(instance=user_profile)
    return render(request, 'user/photo_edit.html', {'form':form})


@login_required
@csrf_exempt  # 开发用
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