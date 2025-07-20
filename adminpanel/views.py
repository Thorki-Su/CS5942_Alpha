from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from task.models import Task, TaskApplication, TaskRecord, Feedback
from django.utils import timezone

User = get_user_model()

def staff_required(view_func):
    """
    Access is only allowed for users with is_staff=True.
    """
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff)(view_func)

@staff_required
def admin_dashboard(request):
    today = timezone.localdate()
    client_count = User.objects.filter(role='client').count()
    volunteer_count = User.objects.filter(role='volunteer').count()
    task_count = Task.objects.count()
    today_task_count = Task.objects.filter(created_at__date=today).count()
    
    context = {
        'client_count': client_count,
        'volunteer_count': volunteer_count,
        'task_count': task_count,
        'today_task_count': today_task_count,
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

@staff_required
def task_list(request):
    tasks = Task.objects.all().order_by('id')
    return render(request, 'adminpanel/task_list.html', {'tasks':tasks})

@staff_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    applications = TaskApplication.objects.filter(task=task)
    records = TaskRecord.objects.filter(task=task)
    feedbacks = Feedback.objects.filter(task=task)

    context = {
        'task': task,
        'applications': applications,
        'records':records,
        'feedbacks':feedbacks,
    }
    return render(request, 'adminpanel/task_detail.html', context)