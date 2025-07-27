# matching/utils.py

from math import radians, cos, sin, asin, sqrt
from task.models import TaskApplication, StarRelation
from user.models import VolunteerProfile, ClientProfile
from django.utils.timezone import localtime, timedelta
from django.urls import reverse
from adminpanel.models import OperationLog


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    计算地球两点之间的距离（单位：公里）
    """
    R = 6371  # 地球半径（km）
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def get_star_score(volunteer_user, client_user):
    score = 0
    if StarRelation.objects.filter(from_user=client_user, to_user=volunteer_user).exists():
        score += 2
    if StarRelation.objects.filter(from_user=volunteer_user, to_user=client_user).exists():
        score += 1
    return score

def match_volunteers_for_task(task):
    """
    根据志愿者设置的排班意向，对新发布的任务进行自动匹配。
    为符合条件的志愿者创建 TaskApplication (pending 状态)
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
    
    # scheduled_volunteers = VolunteerProfile.objects.filter(is_scheduled=True).select_related('user_profile__user').prefetch_related('preferred_tasks')
    scheduled_volunteers = VolunteerProfile.objects.filter(is_scheduled=True)\
        .select_related('user_profile')\
        .prefetch_related('preferred_tasks')

    for profile in scheduled_volunteers:
        user = profile.user_profile.user

        # 跳过已申请该任务的志愿者
        if user.id in existing_app_volunteer_ids:
            # print(f"{user.email} 已申请，跳过")
            continue

        # 冲突检查
        buffer = timedelta(hours=1)
        task_start = task.start_time
        task_end = task.end_time

        # 找到该志愿者已接受的任务（accepted），以及进行中（pending 也可以）
        existing_apps = TaskApplication.objects.filter(
            volunteer=user,
            status__in=['pending', 'accepted'],
            task__start_time__lt=task_end + buffer,
            task__end_time__gt=task_start - buffer,
        )

        if existing_apps.exists():
            continue  # 有冲突，跳过此志愿者

        # 1. 工作内容匹配
        volunteer_support_ids = set(profile.preferred_tasks.values_list('id', flat=True))
        if not task_support_ids & volunteer_support_ids:
            print(f"{user.email} 工作内容不匹配")
            continue

        # 2. 时间匹配
        if task_day not in profile.available_days:
            print(f"{user.email} 可用日期不匹配")
            continue
        if profile.available_start_time and (task_start_time  < profile.available_start_time):
            print(f"{user.email} 可用时间开始早于任务开始")
            continue
        if profile.available_end_time and (task_end_time  > profile.available_end_time):
            print(f"{user.email} 可用时间结束晚于任务结束")
            continue

        # 3. 是否支持宠物
        if not profile.accept_pets and client_has_pets:
            print(f"{user.email} 不接受宠物，任务有宠物")
            continue

        # 4. 距离匹配
        vol_lat = profile.user_profile.location_lat
        vol_lng = profile.user_profile.location_lng
        if None in [vol_lat, vol_lng, client_lat, client_lng]:
            print(f"{user.email} 缺少经纬度信息")
            continue  # 跳过无位置信息者
        distance = haversine_distance(vol_lat, vol_lng, client_lat, client_lng)
        if distance > profile.preferred_distance_km:
            print(f"{user.email} 距离过远,距离{distance},大于{profile.preferred_distance_km}")
            continue

        star_score = get_star_score(user, client_user)
        matched_volunteers.append((star_score, user))

    matched_volunteers.sort(reverse=True, key=lambda x: x[0])
    for _, volunteer in matched_volunteers:
        # 创建申请
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
            print(f"{volunteer.email} 到达任务上限")
        profile.save()

        url = reverse('adminpanel:task_detail', args=[task.id])
        OperationLog.objects.create(
            user=volunteer,
            action=f'Automatically created the application for the task: <a href="{url}">Task #{task.id}</a>',
        )
        matched_count += 1
        print(f"[Match] {volunteer.email} Match successful → Task #{task.id} {task.title}")

    return matched_count
