from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model

User = get_user_model()

def staff_required(view_func):
    """
    Access is only allowed for users with is_staff=True.
    """
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff)(view_func)

@staff_required
def admin_dashboard(request):
    client_count = User.objects.filter(role='client').count()
    volunteer_count = User.objects.filter(role='volunteer').count()
    
    context = {
        'client_count': client_count,
        'volunteer_count': volunteer_count,
    }
    return render(request, 'adminpanel/admin_dashboard.html', context)

@staff_required
def user_list(request):
    users = User.objects.all().order_by('id')
    return render(request, 'adminpanel/user_list.html', {'users': users})

@staff_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'adminpanel/user_detail.html', {'user': user})