from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout,get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import CustomUser, UserProfile, ClientProfile, VolunteerProfile
from ..forms import ClientRegisterForm, ClientProfileForm, VolunteerRegisterForm, VolunteerProfileForm, ProfilePhotoForm
from django.contrib.auth.forms import AuthenticationForm
from django.forms.models import model_to_dict
from django.core.files.base import ContentFile
import base64
import re
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.safestring import mark_safe
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from task.models import Task
from user.utils import geocode_address, is_valid_aberdeen_postcode
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from user.models import CustomUser, UserProfile, ClientProfile, VolunteerProfile
from user.mobile.mobile_forms import MobileClientProfileForm,MobileVolunteerProfileForm
from django.forms.models import model_to_dict

from user.mobile.mobile_utils import safe_model_to_dict

import json

# ------------------------------- Functions below used for mobile app --------------------------------------------------------------
User = get_user_model()

@csrf_exempt
def mobile_client_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            required_fields = ['email', 'password1', 'password2', 'phone', 'address']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'error': f'{field} is required.'}, status=400)

            if data['password1'] != data['password2']:
                return JsonResponse({'error': 'Passwords do not match.'}, status=400)

            # 检查 email 是否已注册
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({'error': 'Email already taken.'}, status=400)

            # 创建用户（email作为唯一标识）
            user = User.objects.create_user(
                email=data['email'],
                password=data['password1'],
                role='client'
            )

            # 创建 user profile（基础信息）
            profile = UserProfile.objects.create(
                user=user,
                phone_number=data['phone'],
                location=data['address'],
                first_name=data.get('first_name', ''),  # 可选字段
                last_name=data.get('last_name', ''),
                consent_safeguard=True  # 默认同意，可按需修改
            )

            # 创建 client profile（即使暂时为空也要创建）
            ClientProfile.objects.create(user_profile=profile)

            return JsonResponse({'success': True, 'message': 'Client registered successfully.'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def mobile_volunteer_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            required_fields = ['email', 'password1', 'password2', 'phone', 'address']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'error': f'{field} is required.'}, status=400)

            if data['password1'] != data['password2']:
                return JsonResponse({'error': 'Passwords do not match.'}, status=400)

            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({'error': 'Email already taken.'}, status=400)

            # 创建用户
            user = User.objects.create_user(
                email=data['email'],
                password=data['password1'],
                role='volunteer'
            )

            # 创建 UserProfile
            profile = UserProfile.objects.create(
                user=user,
                phone_number=data['phone'],
                location=data['address'],
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                consent_safeguard=True
            )

            # 创建 VolunteerProfile（可以后续补充字段）
            VolunteerProfile.objects.create(user_profile=profile)

            return JsonResponse({'success': True, 'message': 'Volunteer registered successfully.'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)

@api_view(['POST'])
def mobile_token_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, email=email, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    # 获取或创建 Token
    token, created = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'email': user.email,
        'role': user.role,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_profile_view(request):
    print("📲 当前是 mobile_profile_view 被调用")
    user = request.user
    user_profile = user.userprofile

    user_fields = safe_model_to_dict(user_profile)
    user_fields['profile_photo'] = user_profile.profile_photo.url if user_profile.profile_photo else None

    user_data = {
        'email': user.email,
        'role': user.role,
        # 'first_name': user.first_name,
        # 'last_name': user.last_name,
        # 'username': user.username,
    }

    result = {
        'user': user_data,
        'user_profile': user_fields,
    }

    if user.role == 'client':
        client_profile = user_profile.clientprofile
        client_fields = safe_model_to_dict(client_profile)
        client_fields['preferred_times'] = client_profile.preferred_times
        client_fields['certifications'] = [c.name for c in client_profile.certifications.all()]
        client_fields['conditions'] = [c.name for c in client_profile.conditions.all()]
        client_fields['support_areas'] = [s.name for s in client_profile.support_areas.all()]
        result['client_fields'] = client_fields

    elif user.role == 'volunteer':
        volunteer_profile = user_profile.volunteerprofile
        volunteer_fields = safe_model_to_dict(volunteer_profile)
        volunteer_fields['availability'] = volunteer_profile.availability
        result['volunteer_fields'] = volunteer_fields

    return Response(result)

@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not user.check_password(old_password):
        return Response({'error': '原密码错误'}, status=400)

    if not new_password or len(new_password) < 8:
        return Response({'error': '新密码长度不能少于 8 位'}, status=400)

    user.set_password(new_password)
    user.save()

    return Response({'status': 'success'})


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_client_profile_edit(request):
    print("🔍 当前用户：", request.user)
    print("🔐 是否认证：", request.user.is_authenticated)

    user_profile = request.user.userprofile
    client_profile = user_profile.clientprofile

    if request.method == 'POST':
        # print('📨 前端传来的 request.data:', request.data)  # 原始 JSON 内容
        # print('📥 request.POST:', request.POST)
        print("📥 conditions 传入值：", request.data.get('conditions'))
        print("📥 support_areas 传入值：", request.data.get('support_areas'))

        # ✅ 更新 user_profile 的字段
        user_profile_fields = [
            field.name for field in user_profile._meta.fields
            if field.name not in ['id', 'user', 'eligibility_confirmed', 'consent_safeguard']
        ]
        for field in user_profile_fields:
            if field in request.data:
                setattr(user_profile, field, request.data.get(field))
        user_profile.save()
        print("✅ UserProfile 保存成功")

        # ✅ 用表单处理 client_profile 的多选字段
        form = MobileClientProfileForm(request.data, request.FILES, instance=client_profile)
        if form.is_valid():
            # 🔥 手动清洗 M2M 字段
            print("正在对M2M字段cleaning中")
            conditions = form.clean_conditions()
            support_areas = form.clean_support_areas()
            certifications = form.clean_certifications()

            print("🧬 清理完成！Cleaned conditions:", conditions)

            instance = form.save(commit=False)
            instance.save()
            instance.conditions.set(conditions)
            instance.support_areas.set(support_areas)
            instance.certifications.set(certifications)

            print("✅ 多选字段已 set")
            return Response({'status': 'success'})
        else:
            print("❌ 表单验证失败，错误信息：", form.errors)
            print('❌ 表单错误详情:', form.errors.as_json())  # ← 错误详情

            return Response({'status': 'error', 'errors': form.errors}, status=400)

    # ✅ GET 请求返回初始数据
    user_data = safe_model_to_dict(user_profile, exclude=['id', 'user', 'profile_photo'])
    client_data = safe_model_to_dict(client_profile, exclude=['id', 'user', 'user_profile'])

    # ✅ 手动补上多对多字段（否则 model_to_dict 不会包含它们）
    client_data['conditions'] = list(client_profile.conditions.values_list('name', flat=True))
    client_data['support_areas'] = list(client_profile.support_areas.values_list('name', flat=True))
    client_data['certifications'] = list(client_profile.certifications.values_list('name', flat=True))
    
    flat_data = {**user_data, **client_data}
    # print("📤 返回前端的 flat_data:", flat_data)
    return Response(flat_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_upload_avatar(request):
    user_profile = request.user.userprofile
    image_data = request.data.get('cropped_image_data')

    if not image_data:
        return Response({'error': 'No image data provided'}, status=400)

    try:
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        file_name = f"{request.user.username}_avatar.{ext}"
        img_data = base64.b64decode(imgstr)
        user_profile.profile_photo.save(file_name, ContentFile(img_data), save=True)
        return Response({'status': 'success'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_save_preferred_times(request):
    user_profile = request.user.userprofile
    client_profile = user_profile.clientprofile
    data = request.data  # 前端传来的 JSON

    print("📥 [Mobile] 接收到 preferred_times:", data)

    if not isinstance(data, dict):
        return Response({'error': 'Invalid format'}, status=400)

    client_profile.preferred_times = data
    client_profile.save()

    return Response({'status': 'success'})

@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def mobile_volunteer_profile_edit(request):
    print("🔍 当前用户：", request.user)
    print("🔐 是否认证：", request.user.is_authenticated)

    user_profile = request.user.userprofile
    volunteer_profile = user_profile.volunteerprofile

    if request.method == 'POST':
        print("📥 preferred_tasks:", request.data.get('preferred_tasks'))
        print("📥 pvg_level:", request.data.get('pvg_level'))

        # ✅ 更新 user_profile 的基础字段
        user_profile_fields = [
            field.name for field in user_profile._meta.fields
            if field.name not in ['id', 'user', 'profile_photo']
        ]
        for field in user_profile_fields:
            if field in request.data:
                setattr(user_profile, field, request.data.get(field))
        user_profile.save()
        print("✅ UserProfile 保存成功")

        # ✅ 表单初始化 + 手动清洗
        form = MobileVolunteerProfileForm(request.data, request.FILES, instance=volunteer_profile)
        if form.is_valid():
            print("✅ 表单验证通过，开始清洗字段")
            print("📥 原始 POST 数据：", request.data)
            preferred_tasks = form.clean_preferred_tasks()
            pvg_level = form.clean_pvg_level()
            # # ✅ 确保清洗后的值写入 cleaned_data
            print("📌 开始保存 preferred_tasks:", preferred_tasks)
            print("📌 类型是：", type(preferred_tasks))
            form.cleaned_data['preferred_tasks'] = preferred_tasks
            form.cleaned_data['pvg_level'] = pvg_level
            print("✅ 表单验证通过")
            instance = form.save(commit=True)  # 让 save 中的逻辑负责写入 set
            print("✅ 多选字段已保存：preferred_tasks + pvg_level")
            return Response({'status': 'success'})
        else:
            print("❌ 表单验证失败，错误信息：", form.errors)
            print("❌ 表单错误详情（as_json）：", form.errors.as_json())
            return Response({'status': 'error', 'errors': form.errors}, status=400)

    # ✅ GET：返回初始 profile 数据
    user_data = safe_model_to_dict(user_profile, exclude=['id', 'user', 'profile_photo'])
    volunteer_data = safe_model_to_dict(volunteer_profile, exclude=[
    'id', 'user', 'user_profile',
    'availability', 'available_days', 'available_start_time', 'available_end_time'
])
    # ✅ 手动补充字段
    volunteer_data['preferred_tasks'] = list(volunteer_profile.preferred_tasks.values_list('name', flat=True))
    volunteer_data['pvg_level'] = volunteer_profile.pvg_level  # 注意：这是字符串，不是 M2M！

    flat_data = {**user_data, **volunteer_data}
    return Response(flat_data)
