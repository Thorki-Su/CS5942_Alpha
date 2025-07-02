from django.contrib import admin
from .models import Task, TaskApplication

# Register your models here.
admin.site.register(Task)
admin.site.register(TaskApplication)