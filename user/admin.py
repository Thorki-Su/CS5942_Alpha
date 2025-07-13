from django.contrib import admin
from .models import ConditionType, CertificationType, SupportType, UserProfile, ClientProfile, VolunteerProfile, CustomUser

admin.site.register(CertificationType)
admin.site.register(ConditionType)
admin.site.register(SupportType)
admin.site.register(UserProfile)
admin.site.register(ClientProfile)
admin.site.register(VolunteerProfile)
admin.site.register(CustomUser)