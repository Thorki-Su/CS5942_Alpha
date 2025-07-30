# matching/utils.py

from math import radians, cos, sin, asin, sqrt
from task.models import TaskApplication, StarRelation
from user.models import VolunteerProfile, ClientProfile
from django.utils.timezone import localtime, timedelta
from django.urls import reverse
from adminpanel.models import OperationLog


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculation of the distance between two points (in kilometres)
    """
    R = 6371  # Earth radius (km)
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def get_star_score(volunteer_user, client_user):
    """
    Give scores based on the stars between users and the scores will be used to compare the priority of matching
    """
    score = 0
    if StarRelation.objects.filter(from_user=client_user, to_user=volunteer_user).exists():
        score += 2
    if StarRelation.objects.filter(from_user=volunteer_user, to_user=client_user).exists():
        score += 1
    return score

def match_volunteers_for_task(task):
    """
    Automated matching of newly posted tasks based on scheduling intentions set by volunteers.
    Create an application for eligible volunteers
    """
    matched_count = 0
    matched_volunteers = []

    task_day = localtime(task.start_time).strftime('%A')
    task_start_time  = localtime(task.start_time).time()
    task_end_time  = localtime(task.end_time).time()
    task_support_ids = set(task.work_area.values_list('id', flat=True))

    client_user = task.client
    client_profile = task.client.userprofile.clientprofile
    client_lat = task.client.userprofile.location_lat
    client_lng = task.client.userprofile.location_lng
    client_has_pets = client_profile.has_pets

    existing_app_volunteer_ids = set(TaskApplication.objects.filter(task=task).values_list('volunteer_id', flat=True))
    
    scheduled_volunteers = VolunteerProfile.objects.filter(is_scheduled=True)\
        .select_related('user_profile')\
        .prefetch_related('preferred_tasks')

    for profile in scheduled_volunteers:
        user = profile.user_profile.user

        # Skip volunteers who have applied for this task
        if user.id in existing_app_volunteer_ids:
            # print(f"DEBUG: {user.email} has applied, skip")
            continue

        # Conflict checking
        buffer = timedelta(hours=1)
        task_start = task.start_time
        task_end = task.end_time
        existing_apps = TaskApplication.objects.filter(
            volunteer=user,
            status__in=['pending', 'accepted'],
            task__start_time__lt=task_end + buffer,
            task__end_time__gt=task_start - buffer,
        )
        if existing_apps.exists():
            continue  # Conflict, skip this volunteer

        # 1. Support Type Matching
        volunteer_support_ids = set(profile.preferred_tasks.values_list('id', flat=True))
        if not task_support_ids & volunteer_support_ids:
            print(f"DEBUG: {user.email} mismatch in support type")
            continue

        # 2. Time Availability
        if task_day not in profile.available_days:
            print(f"DEBUG: {user.email} mismatch in available date")
            continue
        if profile.available_start_time and (task_start_time  < profile.available_start_time):
            print(f"DEBUG: {user.email} available time earlier than the start time")
            continue
        if profile.available_end_time and (task_end_time  > profile.available_end_time):
            print(f"DEBUG: {user.email} available time later than the end time")
            continue

        # 3. Pet Tolerance
        if not profile.accept_pets and client_has_pets:
            print(f"DEBUG: {user.email} no pets accepted, task has pets")
            continue

        # 4. Geographic Distance
        vol_lat = profile.user_profile.location_lat
        vol_lng = profile.user_profile.location_lng
        if None in [vol_lat, vol_lng, client_lat, client_lng]:
            print(f"DEBUG: {user.email} Lack of latitude and longitude information")
            continue  # 跳过无位置信息者
        distance = haversine_distance(vol_lat, vol_lng, client_lat, client_lng)
        if distance > profile.preferred_distance_km:
            print(f"DEBUG: {user.email} too far apart. Practical distance {distance} larger than {profile.preferred_distance_km}")
            continue

        star_score = get_star_score(user, client_user)
        matched_volunteers.append((star_score, user))

    matched_volunteers.sort(reverse=True, key=lambda x: x[0])
    for _, volunteer in matched_volunteers:
        # Create a application
        TaskApplication.objects.create(
            task=task,
            volunteer=volunteer,
            status='pending',
            is_auto_matched=True,
        )
        profile = volunteer.userprofile.volunteerprofile
        profile.assigned_tasks_count += 1
        if profile.assigned_tasks_count >= profile.max_task_count:
            profile.is_scheduled = False
            print(f"DEBUG: {volunteer.email} reaching the task ceiling")
        profile.save()

        url = reverse('adminpanel:task_detail', args=[task.id])
        OperationLog.objects.create(
            user=volunteer,
            action=f'Automatically created the application for the task: <a href="{url}">Task #{task.id}</a>',
        )
        matched_count += 1
        print(f"[Match] {volunteer.email} Match successful → Task #{task.id} {task.title}")

    return matched_count
