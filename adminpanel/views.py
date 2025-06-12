from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

# the view of admin login
def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not an admin.")
            return redirect('admin_login')

    return render(request, 'adminpanel/admin_login.html')

# the view of admin dashboard page
def admin_dashboard_view(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    return render(request, 'adminpanel/admin_dashboard.html', {'user': request.user})
