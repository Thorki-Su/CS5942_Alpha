from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import TaskForm
from django.http import HttpResponseForbidden
from functools import wraps
from .models import Task, TaskApplication
from django.utils import timezone
from datetime import timedelta

# Create your views here.
def client_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role != 'client':
            return HttpResponseForbidden("You do not have permission to access this page")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def volunteer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role != 'volunteer':
            return HttpResponseForbidden("You do not have permission to access this page")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@client_required
def mytask(request):
    tasks = Task.objects.filter(client=request.user).order_by('-start_time')
    for task in tasks:
        task.update_status_if_full()
        task.update_status_by_time()
    return render(request, 'task/mytask.html', {'tasks': tasks})

@login_required
@client_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.client = request.user
            task.status = 'open'
            task.save()
            return redirect('task:mytask')
    else:
        form = TaskForm()

    return render(request, 'task/task_create.html', {'form': form})

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.update_status_by_time()
    user = request.user

    is_client = (user == task.client)

    has_applied = False
    application_status = None
    if hasattr(user, 'volunteerprofile'):
        application = TaskApplication.objects.filter(task=task, volunteer=user).first()
        if application:
            has_applied = True
            application_status = application.status

    context = {
        'task': task,
        'is_client': is_client,
        'has_applied': has_applied,
        'application_status': application_status,
    }
    return render(request, 'task/task_detail.html', context)

@login_required
@client_required
def task_application(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.update_status_by_time()
    applications = TaskApplication.objects.filter(task=task).select_related('volunteer')
    context = {
        'task': task,
        'applications': applications,
    }
    return render(request, 'task/task_application.html', context)

@login_required
@volunteer_required
def myapplication(request):
    user = request.user
    applications = TaskApplication.objects.filter(volunteer=user).select_related('task').order_by('-applied_at')
    return render(request, 'task/myapplication.html', {'applications': applications})

@login_required
@volunteer_required
def tasklist(request):
    user = request.user
    applied_task_ids = TaskApplication.objects.filter(volunteer=user).values_list('task_id', flat=True)
    tasks = Task.objects.filter(status='open').exclude(id__in=applied_task_ids)
    for task in tasks:
        task.update_status_by_time()
    return render(request, 'task/tasklist.html', {'tasks': tasks})

@login_required
def task_ongoing(request):
    user = request.user
    if user.role == 'client':
        tasks = Task.objects.filter(client=user, status='ongoing')
    else:
        tasks = Task.objects.filter(applications__volunteer=user, applications__status='accepted', status='ongoing')
    for task in tasks:
        task.update_status_by_time()
    tasks_with_status = []
    for task in tasks:
        has_accepted_application = (user.role == 'volunteer' and 
                                  task.applications.filter(volunteer=user, status='accepted').exists())
        tasks_with_status.append({
            'task': task,
            'has_accepted_application': has_accepted_application
        })
    
    return render(request, 'task/task_ongoing.html', {
        'tasks_with_status': tasks_with_status,
        'user': user
    })

@login_required
@volunteer_required
def task_apply(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.update_status_by_time()
    user = request.user

    buffer = timedelta(hours=1)  # 任务前后一小时不能有其他任务，不确定，可以再改
    task_start = task.start_time - buffer
    task_end = task.end_time + buffer

    conflicting_apps = TaskApplication.objects.filter(
        volunteer=user,
        status__in=['pending', 'accepted'],
        task__start_time__lt=task_end,
        task__end_time__gt=task_start
    )
    if conflicting_apps.exists():
        messages.error(request, "You have another task near this time. Please check your schedule.")
        return redirect('task:task_detail', task_id=task.id)

    if TaskApplication.objects.filter(task=task, volunteer=request.user).exists():
        messages.warning(request, "You have already applied for the task")
    else:
        TaskApplication.objects.create(task=task, volunteer=request.user, status='pending')
        messages.success(request, "Application successful, please wait for review")

    return redirect('task:task_detail', task_id=task.id)

@login_required
@client_required
def approve_application(request, application_id):
    application = get_object_or_404(TaskApplication, id=application_id)
    task = application.task
    task.update_status_by_time()

    if application.status != 'pending':
        return redirect('task:task_application', task.id)
    
    approved_count = TaskApplication.objects.filter(task=task, status='accepted').count()
    if approved_count >= task.vol_number:
        return redirect('task:task_application', task.id)
    
    application.status = 'accepted'
    application.save()

    if approved_count + 1 >= task.vol_number:
        TaskApplication.objects.filter(task=task, status='pending').update(status='unselected')
        task.status = 'selected'
        task.save()
    return redirect('task:task_application', task.id)

@login_required
@client_required
def reject_application(request, application_id):
    application = get_object_or_404(TaskApplication, id=application_id)
    task = application.task
    task.update_status_by_time()
    if application.status != 'pending':
        return redirect('task:task_application', task.id)
    
    application.status = 'rejected'
    application.save()
    return redirect('task:task_application', task.id)

@login_required
@client_required
def cancel_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.update_status_by_time()
    
    if request.method == 'POST':
        task.cancel()
        return redirect('task:mytask')

    return redirect('task:task_detail', task_id=task.id)

@login_required
@volunteer_required
def cancel_application(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.update_status_by_time()
    user = request.user
    application = TaskApplication.objects.filter(task=task, volunteer=user).first()

    if request.method == 'POST':
        application.cancel()
        return redirect('task:myapplication')
    
    return redirect('task:task_detail', task_id=task.id)