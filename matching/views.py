from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from user.models import VolunteerProfile, UserProfile
from .models import MatchRecord
import uuid
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages


@login_required
def match_page(request):
    return render(request, 'matching/match.html')


@login_required
def volunteer_list(request):
    volunteers = VolunteerProfile.objects.select_related('user_profile__user').all()
    return render(request, 'matching/volunteer_list.html', {'volunteers': volunteers})


@login_required
def match_specific_volunteer(request, volunteer_id):
    current_user = request.user

    if request.method == 'POST':
        try:
            # 当前用户必须是 client
            if current_user.role != 'client':
                messages.error(request, "只有用户角色为 client 的用户才能进行匹配。")
                return redirect('volunteer_list')

            # 获取 client 和 volunteer 信息
            client_profile = UserProfile.objects.get(user=current_user)
            volunteer_profile = VolunteerProfile.objects.get(id=volunteer_id)
            volunteer_user = volunteer_profile.user_profile.user

            # 避免重复匹配（可选）
            if MatchRecord.objects.filter(client=current_user, volunteer=volunteer_user).exists():
                messages.info(request, "你已匹配过该志愿者。")
                return redirect('volunteer_list')

            # 生成会议信息
            meeting_id = str(uuid.uuid4())[:8]
            match_time = timezone.now()
            time_slot = "Sunday 14:00-17:00"  # 示例，可动态生成

            MatchRecord.objects.create(
                client=current_user,
                volunteer=volunteer_user,
                client_email=current_user.email,
                volunteer_email=volunteer_user.email,
                match_time=match_time,
                time_slot=time_slot,
                meeting_id=meeting_id
            )

            messages.success(request, f"匹配成功！会议号为：{meeting_id}")
            return redirect('volunteer_list')

        except Exception as e:
            messages.error(request, f"匹配失败：{str(e)}")
            return redirect('volunteer_list')

    return HttpResponseRedirect('/volunteer-list/')
