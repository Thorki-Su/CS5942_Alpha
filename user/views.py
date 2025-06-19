from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# from django.contrib import messages
from .models import CustomUser, UserProfile, ClientProfile, VolunteerProfile
from .forms import ClientRegisterForm, ClientProfileForm, VolunteerRegisterForm, VolunteerProfileForm
from django.contrib.auth.forms import AuthenticationForm

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
    # if request.method == 'POST':
    #     username = request.POST.get('username')
    #     password = request.POST.get('password')

    #     user = authenticate(request, username=username, password=password)
    #     if user is not None:
    #         login(request, user)
    #         return redirect('dashboard')
    #     else:
    #         messages.error(request, "Wrong username or password.")
    #         return redirect('login')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            #return redirect('client_profile_detail')
            return redirect('user:home')
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
            return redirect('user:client_profile_edit')
        else:
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
            return redirect('user:volunteer_profile_edit')
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
            return redirect('user:client_profile_detail')
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
            return redirect('user:volunteer_profile_detail')
    else:
        form = VolunteerProfileForm(instance=volunteer_profile)
    return render(request, 'user/volunteer_profile_edit.html', {'form':form})

@login_required
def client_profile_detail(request):
    client_profile = request.user.userprofile.clientprofile
    return render(request, 'user/client_profile_detail.html', {'client_profile':client_profile})

@login_required
def volunteer_profile_detail(request):
    volunteer_profile = request.user.userprofile.volunteerprofile
    return render(request, 'user/volunteer_profile_detail.html', {'client_profile':volunteer_profile})