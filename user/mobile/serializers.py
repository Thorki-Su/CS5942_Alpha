# user/mobile/serializers.py

from rest_framework import serializers
from user.models import CustomUser, UserProfile
from task.models import Task

class SimpleVolunteerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name']

    def get_full_name(self, obj):
        if hasattr(obj, 'userprofile'):
            return obj.userprofile.get_full_name
        return None
    
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'start_time', 'end_time', 'status', 'vol_number', 'work_area']
