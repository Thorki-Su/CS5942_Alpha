from django.contrib import admin
from .models import Task, TaskApplication, TaskTemplate, TaskRecord, Feedback, StarRelation

# Register your models here.
admin.site.register(Task)
admin.site.register(TaskApplication)
admin.site.register(TaskTemplate)
admin.site.register(TaskRecord)
admin.site.register(Feedback)
admin.site.register(StarRelation)