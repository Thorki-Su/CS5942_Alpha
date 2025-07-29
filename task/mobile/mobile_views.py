from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from task.models import Task,TaskApplication,Feedback,CustomUser,TaskRecord
from user.models import SupportType
from user.mobile.serializers import SimpleVolunteerSerializer,TaskSerializer
import json
from django.db.models import Q
from django.shortcuts import get_object_or_404

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_available_tasks(request):
    user = request.user

    # volunteer 用户只能看到 status=open 且没申请过的任务
    applied_task_ids = TaskApplication.objects.filter(volunteer=user).values_list('task_id', flat=True)
    tasks = Task.objects.filter(status='open').exclude(id__in=applied_task_ids).order_by('-created_at')

    keyword = request.GET.get('keyword', '').strip()
    weekday = request.GET.get('weekday', '')
    time_block = request.GET.get('time_block', '')
    work_area = request.GET.get('work_area', '')  # 可传 ID 或 name
    print(f"🔍 Received keyword: {keyword}")

    if keyword:
        tasks = tasks.filter(
            Q(title__icontains=keyword) |
            Q(description__icontains=keyword)
        )

    if work_area:
        tasks = tasks.filter(work_area__name=work_area)

    if weekday != '':
        try:
            weekday_int = int(weekday)
            django_weekday = (weekday_int + 2) % 7 or 7
            tasks = tasks.filter(start_time__week_day=django_weekday)
        except ValueError:
            pass

    if time_block:
        from datetime import time
        time_ranges = {
            'morning': (time(8, 0), time(11, 0)),
            'midday': (time(11, 0), time(14, 0)),
            'afternoon': (time(14, 0), time(17, 0)),
        }
        if time_block in time_ranges:
            start, end = time_ranges[time_block]
            tasks = tasks.filter(start_time__time__gte=start, start_time__time__lt=end)

    serializer = TaskSerializer(tasks, many=True)
    return Response({'tasks': serializer.data})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_create_task(request):
    user = request.user

    # 确保是 Client 身份
    if user.role != 'client':
        return Response({'error': 'Only clients can create tasks.'}, status=403)

    data = request.data
    print("📥 收到的请求数据:", data)
    required_fields = ['title', 'description', 'start_time', 'end_time','vol_number', 'work_area' ]
    for field in required_fields:
        if not data.get(field):
            print(f"❌ 缺失字段：{field}，值为：{data.get(field)}")
            return Response({'error': f'{field} is required.'}, status=400)
    try:
        # ✅ 创建任务本体
        task = Task.objects.create(
            client=user,
            title=data['title'],
            description=data['description'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            vol_number=data['vol_number'],
            status='open',
        )

        # ✅ 设置 work_area 多对多字段（用 name 匹配 SupportType）
        work_area_names = data['work_area']  # 可能是 list 或 json 字符串
        if isinstance(work_area_names, list):
            print("🔍 work_area 以 list 接收")
            selected_ids = list(SupportType.objects.filter(name__in=work_area_names).values_list('id', flat=True))
        else:
            print("🌀 work_area 是字符串，尝试 json.loads")
            try:
                raw = json.loads(work_area_names)
                selected_ids = list(SupportType.objects.filter(name__in=raw).values_list('id', flat=True))
            except Exception as e:
                print("❌ work_area 反序列化失败:", str(e))
                return Response({'error': f'Invalid work_area format: {str(e)}'}, status=400)

        task.work_area.set(selected_ids)

        print(f"✅ 创建成功，任务ID: {task.id}, 支持领域: {selected_ids}")
        return Response({'success': True, 'task_id': task.id})

    except Exception as e:
        print("❌ 创建任务失败:", str(e))
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mobile_work_areas(request):
    work_areas = SupportType.objects.all()
    data = [{'label': wa.name, 'value': wa.id} for wa in work_areas]
    return Response(data)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_my_tasks(request):
    user = request.user

    if user.role != 'client':
        return Response({'error': 'Only clients can view their tasks.'}, status=403)

    tasks = Task.objects.filter(client=user).order_by('-created_at')

    task_list = [
        {
            'id': t.id,
            'title': t.title,
            'description': t.description,
            # 'date': t.date,
            'start_time': t.start_time,
            'end_time': t.end_time,
            'created_at': t.created_at,
            # 'location': t.location,
            'status': t.status,
            'vol_number': t.vol_number,
            'work_area': [area.name for area in t.work_area.all()],
        }
        for t in tasks
    ]

    return Response({'tasks': task_list})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_task_detail(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        task.update_status_by_time()
    except Task.DoesNotExist:
        return Response({'error': 'Task not found.'}, status=404)
    
    # 查找当前用户提交的反馈（可选）
    # ✅ 返回当前用户作为发出者的反馈（from_user = request.user）
    feedback = Feedback.objects.filter(task=task, from_user=request.user).first()
    feedback_data = {
        'is_satisfied': feedback.is_satisfied,
        'comment': feedback.comment,
        'submitted_at': feedback.submitted_at,
    } if feedback else None
    # ✅ 返回当前用户作为接收者的反馈（to_user = request.user）
    received_feedback = Feedback.objects.filter(task=task, to_user=request.user).first()
    received_data = {
        'is_satisfied': received_feedback.is_satisfied,
        'comment': received_feedback.comment,
        'from_user_name': received_feedback.from_user.userprofile.get_full_name,
    } if received_feedback else None

    return Response({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'start_time': task.start_time,
        'end_time': task.end_time,
        'status': task.status,
        'vol_number': task.vol_number,
        'work_area': [area.name for area in task.work_area.all()],
        'creator': task.client.userprofile.get_full_name,  # ✅
        'created_at': task.created_at,                      # ✅
        'closed_at': task.closed_at,                        # ✅ 可能为 None
        'feedback': feedback_data,
        'received_feedback': received_data, 
        'accepted_volunteers': [
            {
                'id': v.volunteer.id,
                'name': v.volunteer.userprofile.get_full_name,
                'email': v.volunteer.email,
                'has_feedback': Feedback.objects.filter(
                    task=task,
                    from_user=request.user,
                    to_user=v.volunteer
                ).exists()
            }
            for v in task.applications.filter(status='accepted')
        ],
        'volunteer_submitted': task.volunteer_submitted,
        'confirmed_by_client': task.confirmed_by_client,
        'can_confirm': task.status == 'ongoing' and task.volunteer_submitted,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_approve_application(request, task_id, application_id):
    print(f"📥 Received approval request for application ID: {application_id}")
    
    try:
        app = TaskApplication.objects.get(id=application_id)
        task = app.task

        if task.id != task_id:
            return Response({'error': 'Task ID mismatch'}, status=400)
        if task.client != request.user:
            return Response({'error': 'Permission denied'}, status=403)

        if app.status != 'pending':
            return Response({'error': 'Application is not pending'}, status=400)

        # ✅ 改状态为 accepted
        app.status = 'accepted'
        app.save()

        # ✅ 主动更新任务状态
        task.update_status_if_full()

        # ✅ 如果此时时间在进行中，并且任务不是 ongoing，就变为 ongoing
        now = timezone.now()
        if task.start_time <= now <= task.end_time + timedelta(hours=2):
            if task.status != 'ongoing':
                task.status = 'ongoing'
                task.applications.filter(status='pending').update(status='unselected')
                task.save()

        print(f"✅ Application {application_id} approved, task {task_id} status: {task.status}")
        return Response({'message': 'Application approved'})

    except TaskApplication.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_reject_application(request, task_id, application_id):
    print(f"📥 Received rejection request for application ID: {application_id}")
    try:
        app = TaskApplication.objects.get(id=application_id)
        task = app.task

        if task.id != task_id:
            return Response({'error': 'Task ID mismatch'}, status=400)
        if task.client != request.user:
            return Response({'error': 'Permission denied'}, status=403)

        if app.status != 'pending':
            return Response({'error': 'Only pending applications can be rejected'}, status=400)

        print(f"📥 已经拒绝了 {application_id} 的申请")
        app.status = 'rejected'
        app.save()

        # ✅ 更新任务的状态（如是否已满、是否变为 ongoing）
        task.update_status_if_full()

        now = timezone.now()
        if task.start_time <= now <= task.end_time + timedelta(hours=2):
            approved_count = task.applications.filter(status='accepted').count()
            if approved_count > 0 and task.status != 'ongoing':
                task.status = 'ongoing'
                task.applications.filter(status='pending').update(status='unselected')
                task.save()

        return Response({'message': 'Application rejected'})

    except TaskApplication.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_cancel_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, client=request.user)
        task.status = 'cancelled'
        task.save()
        return Response({'message': 'Task cancelled successfully'})
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
# 此为role === volunteer 时申请task的后端
def mobile_apply_for_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, status='open')
    except Task.DoesNotExist:
        return Response({'error': 'Task not found or closed'}, status=404)

    if TaskApplication.objects.filter(task=task, volunteer=request.user).exists():
        return Response({'error': 'Already applied'}, status=400)

    TaskApplication.objects.create(task=task, volunteer=request.user, status='pending')
    return Response({'message': 'Application submitted'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_cancel_application(request, application_id):
    try:
        app = TaskApplication.objects.get(id=application_id)

        if app.volunteer != request.user:
            return Response({'error': 'Permission denied'}, status=403)
        
        if app.status != 'pending':
            return Response({'error': 'Only pending applications can be cancelled'}, status=400)

        app.status = 'cancelled'
        app.save()
        return Response({'message': 'Application cancelled'})
    except TaskApplication.DoesNotExist:
        return Response({'error': 'Application not found'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_volunteer_applications(request):
    user = request.user
    applications = TaskApplication.objects.filter(volunteer=user).order_by('-applied_at')

    data = []
    print("📤 Volunteer Applications Fetched:")
    for app in applications:
        # print("📦 Application ID:", app.id, "➡️ Client ID:", app.task.client.id)
        # print("👀 Client:", app.task.client, "🧬 Type:", type(app.task.client))  # ✅ 调试用
        data.append({
            'id': app.id,
            'task_id': app.task.id,
            'title': app.task.title,
            'start_time': app.task.start_time,
            'end_time': app.task.end_time,
            'status': app.status,
            'task_status': app.task.status,
            'applied_at': app.applied_at,
            'client_id': app.task.client.id,
        })
    return Response({'applications': data})
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_task_applications(request, task_id):
    applications = TaskApplication.objects.filter(task_id=task_id).select_related('volunteer__userprofile')
    data = []
    for app in applications:
        volunteer_data = SimpleVolunteerSerializer(app.volunteer).data
        data.append({
            'id': app.id,
            'volunteer': volunteer_data,
            'status': app.status,
            'is_auto_matched': app.is_auto_matched,
        })
    return Response({'applications': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_volunteer_feedback(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        from_user = request.user
        to_user = task.client

        # 检查是否允许反馈（测试阶段可接受 accepted）
        application = TaskApplication.objects.filter(task=task, volunteer=from_user, status='accepted').first()
        if not application or task.status != 'completed':
            return Response({'error': 'Feedback is only allowed for completed tasks you participated in.'}, status=403)

        if Feedback.objects.filter(task=task, from_user=from_user, to_user=to_user).exists():
            return Response({'error': 'Feedback already submitted.'}, status=400)

        is_satisfied = request.data.get('is_satisfied')
        comment = request.data.get('comment', '')

        Feedback.objects.create(
            task=task,
            from_user=from_user,
            to_user=to_user,
            is_satisfied=is_satisfied,
            comment=comment
        )
        return Response({'message': 'Feedback submitted.'})
    except Task.DoesNotExist:
        return Response({'error': 'Task not found.'}, status=404)
    
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def mobile_client_feedback(request, task_id, volunteer_id):
    try:
        task = Task.objects.get(id=task_id)
        from_user = request.user  # client

        if task.client != from_user:
            return Response({'error': 'You are not the owner of this task.'}, status=403)

        # ✅ GET: 返回反馈信息
        if request.method == 'GET':
            volunteer = CustomUser.objects.get(id=volunteer_id)
            # Client 给 volunteer 的反馈
            feedback = Feedback.objects.filter(task=task, from_user=from_user, to_user=volunteer).first()

            # Volunteer 给 client 的反馈
            volunteer_feedback = Feedback.objects.filter(task=task, from_user=volunteer, to_user=from_user).first()

            return Response({
                'task_title': task.title,
                'volunteer_name': volunteer.userprofile.get_full_name,
                'feedback': {
                    'is_satisfied': feedback.is_satisfied,
                    'comment': feedback.comment,
                    'submitted_at': feedback.submitted_at
                } if feedback else None,
                'volunteer_feedback': {
                    'is_satisfied': volunteer_feedback.is_satisfied,
                    'comment': volunteer_feedback.comment,
                    'submitted_at': volunteer_feedback.submitted_at
                } if volunteer_feedback else None,
            })

        # ✅ POST: 提交反馈
        elif request.method == 'POST':
            if Feedback.objects.filter(task=task, from_user=from_user, to_user_id=volunteer_id).exists():
                return Response({'error': 'Feedback already submitted.'}, status=400)

            Feedback.objects.create(
                task=task,
                from_user=from_user,
                to_user_id=volunteer_id,
                is_satisfied=request.data.get('is_satisfied'),
                comment=request.data.get('comment', '')
            )
            return Response({'message': 'Feedback submitted.'})

    except Task.DoesNotExist:
        return Response({'error': 'Task not found.'}, status=404)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_submit_task_record(request, task_id):
    """
    移动端：志愿者提交任务记录
    """
    user = request.user
    task = get_object_or_404(Task, id=task_id)

    # 确保是该任务的 accepted 志愿者
    application = TaskApplication.objects.filter(
        task=task,
        volunteer=user,
        status='accepted'
    ).first()

    if not application:
        return Response({'error': 'You are not authorized to submit records for this task.'}, status=403)

    # 提交记录
    records = request.data.get('records')
    if not isinstance(records, list) or not records:
        return Response({'error': 'Records must be a non-empty list.'}, status=400)

    # 保存或更新记录
    TaskRecord.objects.update_or_create(
        task=task,
        volunteer=user,
        defaults={'records': records}
    )

    # 设置 task 标记为志愿者已提交记录
    task.volunteer_submitted = True
    task.save()
    # print('表单提交成功')

    return Response({'message': 'Task record submitted successfully.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def force_complete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)

    if task.client != request.user:
        return Response({'detail': 'You are not authorized to modify this task.'}, status=status.HTTP_403_FORBIDDEN)

    if task.status != 'ongoing':
        return Response({'detail': 'Only ongoing tasks can be force-completed.'}, status=status.HTTP_400_BAD_REQUEST)

    if task.confirmed_by_client:
        return Response({'detail': 'This task has already been marked as completed.'}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ 提前结束任务，但不设为 completed
    task.end_time = timezone.now()  # ⏱ 设置结束时间为现在
    task.save()

    return Response({'detail': 'Task forcefully marked as completed.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_get_task_record(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        if request.user != task.client:
            return Response({'error': 'Only the client can view this record'}, status=403)

        record = TaskRecord.objects.get(task=task)
        return Response({
            'task_id': record.task.id,
            'volunteer_id': record.volunteer.id,
            'volunteer_name': record.volunteer.userprofile.get_full_name,
            'submitted_at': record.submitted_at,
            'records': record.records,
        })
    except TaskRecord.DoesNotExist:
        return Response({'error': 'No record found for this task'}, status=404)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_confirm_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        if request.user != task.client:
            return Response({'error': 'Permission denied'}, status=403)

        if not task.volunteer_submitted:
            return Response({'error': 'Volunteer has not submitted records yet.'}, status=400)

        task.confirmed_by_client = True
        task.status = 'completed'
        task.closed_at = timezone.now()
        task.save()

        return Response({'message': 'Task confirmed and marked as completed.'})
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=404)