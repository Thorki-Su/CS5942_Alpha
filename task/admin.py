from django.contrib import admin
from .models import Task, TaskApplication, TaskTemplate

# Register your models here.
admin.site.register(Task)
admin.site.register(TaskApplication)
admin.site.register(TaskTemplate)