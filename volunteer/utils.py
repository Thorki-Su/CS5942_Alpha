from datetime import timedelta
from django.db.models import Q
from task.models import TaskApplication


def calculate_volunteer_duration(volunteer_user):
    """
    Calculate total duration a volunteer has spent on completed tasks.
    Returns total duration in hours as a float.
    """
    # Get all completed task applications for this volunteer
    completed_applications = TaskApplication.objects.filter(
        volunteer=volunteer_user,
        status='completed'
    ).select_related('task')
    
    total_duration = timedelta()
    
    for application in completed_applications:
        task = application.task
        # Calculate duration between task start and end time
        task_duration = task.end_time - task.start_time
        total_duration += task_duration
    
    # Convert to hours (as float)
    total_hours = total_duration.total_seconds() / 3600
    return total_hours


def format_volunteer_duration(total_hours):
    """
    Format volunteer duration into a readable string.
    Returns formatted string like "25 hours 30 minutes" or "2 days 3 hours"
    """
    if total_hours == 0:
        return "0 hours"
    
    # Convert to days, hours, and minutes
    total_minutes = int(total_hours * 60)
    days = total_minutes // (24 * 60)
    remaining_minutes = total_minutes % (24 * 60)
    hours = remaining_minutes // 60
    minutes = remaining_minutes % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 and days == 0:  # Only show minutes if less than a day
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    if not parts:
        return "0 hours"
    
    return " ".join(parts)