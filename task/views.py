from django.shortcuts import render

# Create your views here.
def mytask(request):
    return render(request, 'task/mytask.html')

def task_create(request):
    return render(request, 'task/task_create.html')

def task_detail(request):
    return render(request, 'task/task_detail.html')

def task_application(request):
    return render(request, 'task/task_application.html')

def myapplication(request):
    return render(request, 'task/myapplication.html')

def tasklist(request):
    return render(request, 'task/tasklist.html')

def task_ongoing(request):
    return render(request, 'task/task_ongoing.html')