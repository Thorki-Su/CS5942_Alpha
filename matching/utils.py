# matching/utils.py

from math import radians, cos, sin, asin, sqrt
from task.models import TaskApplication
from user.models import VolunteerProfile, ClientProfile
from django.utils.timezone import localtime


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


def match_volunteers_for_task(task):
    """
    根据志愿者设置的排班意向，对新发布的任务进行自动匹配。
    为符合条件的志愿者创建 TaskApplication (pending 状态)
    """
    matched_count = 0

    task_day = localtime(task.start_time).strftime('%A')
    task_start = localtime(task.start_time).time()
    task_end = localtime(task.end_time).time()
    task_support_ids = set(task.work_area.values_list('id', flat=True))

    client_profile = task.client.userprofile.clientprofile
    client_lat = task.client.userprofile.location_lat
    client_lng = task.client.userprofile.location_lng
    client_has_pets = client_profile.has_pets

    scheduled_volunteers = VolunteerProfile.objects.filter(is_scheduled=True).select_related('user_profile__user').prefetch_related('preferred_tasks')

    for profile in scheduled_volunteers:
        user = profile.user_profile.user

        # 跳过已申请该任务的志愿者
        if TaskApplication.objects.filter(task=task, volunteer=user).exists():
            print(f"{user.email} 已申请，跳过")
            continue

        # 1. 工作内容匹配
        volunteer_support_ids = set(profile.preferred_tasks.values_list('id', flat=True))
        if not task_support_ids & volunteer_support_ids:
            print(f"{user.email} 工作内容不匹配")
            continue

        # 2. 时间匹配
        if task_day not in profile.available_days:
            print(f"{user.email} 可用日期不匹配")
            continue
        if profile.available_start_time and (task_start < profile.available_start_time):
            print(f"{user.email} 可用时间开始早于任务开始")
            continue
        if profile.available_end_time and (task_end > profile.available_end_time):
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
            print(f"{user.email} 距离过远")
            continue

        # 创建申请
        TaskApplication.objects.create(
            task=task,
            volunteer=user,
            status='pending',
            is_auto_matched=True,
        )
        matched_count += 1

    return matched_count
