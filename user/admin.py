from django.contrib import admin
from .models import ConditionType, CertificationType

# Register your models here.
admin.site.register(CertificationType)
admin.site.register(ConditionType)