from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def home_view(request):
    return render(request, 'home.html')

# The view of register
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "The two passwords are inconsistent.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "The user name already exists.")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, "Registration is successful, please log in.")
        return redirect('login')

    return render(request, 'register.html')


#  The view of login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Wrong username or password.")
            return redirect('login')

    return render(request, 'login.html')


# the view of log out
def logout_view(request):
    logout(request)
    return redirect('login')


# the view of page
def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'dashboard.html', {'user': request.user})



