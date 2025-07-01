from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def mytask(request):
    return render(request, 'task/mytask.html')

@login_required
def task_create(request):
    return render(request, 'task/task_create.html')

@login_required
def task_detail(request):
    return render(request, 'task/task_detail.html')

@login_required
def task_application(request):
    return render(request, 'task/task_application.html')

@login_required
def myapplication(request):
    return render(request, 'task/myapplication.html')

@login_required
def tasklist(request):
    return render(request, 'task/tasklist.html')

@login_required
def task_ongoing(request):
    return render(request, 'task/task_ongoing.html')