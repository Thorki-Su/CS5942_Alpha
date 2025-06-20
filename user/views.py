from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, UserProfile, ClientProfile, VolunteerProfile
from .forms import ClientRegisterForm, ClientProfileForm, VolunteerRegisterForm, VolunteerProfileForm
from django.contrib.auth.forms import AuthenticationForm
from django.forms.models import model_to_dict

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
            return redirect('login')
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
        return redirect('user:client_profile_edit')
    if request.method == 'POST':
        form = ClientProfileForm(request.POST, request.FILES, instance=client_profile)
        if form.is_valid():
            form.save()
            profile_photo_file = form.cleaned_data.get('profile_photo') #手动保存图片
            if profile_photo_file:
                user_profile = request.user.userprofile
                user_profile.profile_photo = profile_photo_file
                user_profile.save()
            return redirect('user:profile_detail')
        else: #同理
            print(form.errors)
    else:
        form = ClientProfileForm(instance=client_profile)
    return render(request, 'user/client_profile_edit.html', {'form':form})

@login_required
def volunteer_profile_edit(request):
    try:
        volunteer_profile = request.user.userprofile.volunteerprofile
    except VolunteerProfile.DoesNotExist:
        return redirect('user:volunteer_profile_edit')
    if request.method == 'POST':
        form = VolunteerProfileForm(request.POST, request.FILES, instance=volunteer_profile)
        if form.is_valid():
            form.save()
            profile_photo_file = form.cleaned_data.get('profile_photo') #同理
            if profile_photo_file:
                user_profile = request.user.userprofile
                user_profile.profile_photo = profile_photo_file
                user_profile.save()
            return redirect('user:profile_detail')
    else:
        form = VolunteerProfileForm(instance=volunteer_profile)
    return render(request, 'user/volunteer_profile_edit.html', {'form':form})

@login_required
def profile_detail(request):
    user = request.user
    user_profile = user.userprofile
    user_fields = model_to_dict(user_profile)
    if user.role == 'client':
        client_profile = user_profile.clientprofile
        client_fields = model_to_dict(client_profile)
        cert_list = client_profile.certifications.all()
        has_pip_cert = any(c.name == 'PIP' for c in cert_list)
        has_adp_cert = any(c.name == 'ADP' for c in cert_list)
        has_lwc_cert = any(c.name == 'LWC' for c in cert_list)
        context = {
            'user':user,
            'user_profile':user_profile,
            'client_profile':client_profile,
            'user_fields':user_fields,
            'client_fields':client_fields,
            'has_pip_cert':has_pip_cert,
            'has_adp_cert':has_adp_cert,
            'has_lwc_cert':has_lwc_cert,
        }
    elif user.role == 'volunteer':
        volunteer_profile = user_profile.volunteerprofile
        volunteer_fields = model_to_dict(volunteer_profile)
        context = {
            'user':user,
            'user_profile':user_profile,
            'volunteer_profile':volunteer_profile,
            'user_fields':user_fields,
            'volunteer_fields':volunteer_fields,
        }
    return render(request, 'user/profile_detail.html', context=context)
