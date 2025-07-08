from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import TaskForm, TaskFilterForm, TaskRecordForm
from django.http import HttpResponseForbidden
from functools import wraps
from .models import Task, TaskApplication, TaskTemplate, TaskRecord
from django.utils import timezone
from datetime import timedelta, time
from django.db.models import Q

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
    templates = TaskTemplate.objects.prefetch_related('work_area').all()

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.client = request.user
            task.status = 'open'
            task.save()
            form.save_m2m()
            return redirect('task:mytask')
    else:
        form = TaskForm()

    return render(request, 'task/task_create.html', {
        'form': form,
        'templates': templates
        })

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.update_status_by_time()
    user = request.user

    is_client = (user == task.client)

    # has_applied = False
    # application_status = None
    # be_accepted = False
    # if hasattr(user, 'volunteerprofile'):
    #     application = TaskApplication.objects.filter(task=task, volunteer=user).first()
    #     if application:
    #         has_applied = True
    #         application_status = application.status
    #     if application_status == 'accepted':
    #         be_accepted =True
    application = TaskApplication.objects.filter(task=task, volunteer=user).first()
    has_applied = application is not None
    application_status = application.status if application else None
    be_accepted = application_status == 'accepted'

    context = {
        'task': task,
        'is_client': is_client,
        'has_applied': has_applied,
        'application_status': application_status,
        'be_accepted': be_accepted,
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
    form = TaskFilterForm(request.GET or None)
    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        weekday = form.cleaned_data.get('weekday')
        time_block = form.cleaned_data.get('time_block')
        work_area = form.cleaned_data.get('work_area')

        if keyword:
            tasks = tasks.filter(
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword)
            )

        if work_area:
            tasks = tasks.filter(work_area__in=[work_area])

        if weekday != '':
            weekday_int = int(weekday)
            # Django 中 week_day: Sunday = 1, Monday = 2, ..., Saturday = 7
            # 而 Python datetime.weekday(): Monday = 0
            # 所以 weekday + 2，再 % 7，然后处理 Sunday = 7
            django_weekday = (weekday_int + 2) % 7 or 7
            tasks = tasks.filter(start_time__week_day=django_weekday)

        if time_block:
            time_ranges = {
                'morning': (time(8, 0), time(11, 0)),
                'midday': (time(11, 0), time(14, 0)),
                'afternoon': (time(14, 0), time(17, 0)),
            }
            start, end = time_ranges[time_block]
            tasks = tasks.filter(start_time__time__gte=start, start_time__time__lt=end)
    
    for task in tasks:
        task.update_status_by_time()

    return render(request, 'task/tasklist.html', {
        'tasks': tasks, 
        'form': form
    })

@login_required
def task_ongoing(request):
    user = request.user
    related_tasks = Task.objects.filter(
        Q(client=user) | 
        Q(applications__volunteer=user)
    ).distinct()

    for task in related_tasks:
        task.update_status_by_time()

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

    # if approved_count + 1 >= task.vol_number:
    #     TaskApplication.objects.filter(task=task, status='pending').update(status='unselected')
    #     task.status = 'selected'
    #     task.save()
    application.status = 'accepted'
    application.save()
    task.update_status_if_full()
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
        if task.is_within_24h():
            messages.error(request, "Cannot cancel a task less than 24 hours before it starts.")
        else:
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
        if not application.can_be_cancelled():
            messages.error(request, "You cannot cancel this application within 24 hours of task start.")
        else:
            application.cancel()
        return redirect('task:myapplication')
    
    return redirect('task:task_detail', task_id=task.id)

@login_required
@client_required
def task_confirm(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.update_status_by_time()

    if request.user != task.client or not task.volunteer_submitted:
        return redirect('task:task_detail', task_id=task.id)
    
    record = getattr(task, 'record', None)
    if request.method == 'POST':
        task.confirmed_by_client = True
        task.status = 'completed'
        task.closed_at = timezone.now()
        task.save()
        return redirect('task:mytask')
    
    return render(request, 'task/task_confirm.html', {'task': task, 'record': record})

@login_required
@volunteer_required
def task_record(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.update_status_by_time()
    if not TaskApplication.objects.filter(task=task, volunteer=request.user, status='accepted').exists():
        return redirect('task:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        records = [value for key, value in request.POST.items() if key.startswith('record_') and value.strip()]
        if records:
            TaskRecord.objects.update_or_create(
                task=task,
                volunteer=request.user,
                defaults={'records': records}
            )
            task.volunteer_submitted = True
            task.save()
            return redirect('task:task_detail', task_id=task.id)
    return render(request, 'task/task_record.html')