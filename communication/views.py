from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from task.models import Task, TaskApplication
from .models import OneToOneChatSession
from asgiref.sync import sync_to_async, async_to_sync
from django.urls import reverse
from django.core.paginator import Paginator
import asyncio
import logging

# 配置日志
logger = logging.getLogger(__name__)

@sync_to_async
def get_or_create_one_to_one_room(user1_email, user2_email):
    User = get_user_model()
    try:
        print(f"Attempting to get or create room for {user1_email} and {user2_email}")  # 调试日志
        user1 = User.objects.get(email=user1_email, is_active=True)
        print(f"Found user1: {user1.email}, id={user1.id}, is_active={user1.is_active}")  # 调试日志
        user2 = User.objects.get(email=user2_email, is_active=True)
        print(f"Found user2: {user2.email}, id={user2.id}, is_active={user2.is_active}")  # 调试日志
        user_ids = sorted([user1.id, user2.id])
        room_name = f"1v1_{user_ids[0]}_{user_ids[1]}"
        print(f"Generated room_name: {room_name}")  # 调试日志
        existing_sessions = OneToOneChatSession.objects.filter(user1__id__in=[user1.id, user2.id], user2__id__in=[user1.id, user2.id])
        if existing_sessions.exists():
            print(f"Existing session found: {existing_sessions[0].room_name}")
            return existing_sessions[0].room_name
        try:
            session, created = OneToOneChatSession.objects.get_or_create(
                user1=user1,
                user2=user2,
                defaults={'room_name': room_name}
            )
            print(f"Created OneToOneChatSession: room_name={room_name}, created={created}, session={session}")  # 调试日志
        except Exception as e:
            logger.error(f"Database save error: {e}")
            raise
        return session.room_name
    except User.DoesNotExist as e:
        logger.error(f"User not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_or_create_one_to_one_room: {e}")
        raise

@login_required
def message_selection_view(request):
    return render(request, 'communication/message_selection.html')

@login_required
def one_to_one_chat_selection_view(request):
    User = get_user_model()
    # 获取搜索关键字
    search_query = request.GET.get('q', '').strip()
    users = User.objects.exclude(email=request.user.email).filter(is_active=True)
    if search_query:
        users = users.filter(email__icontains=search_query)
    
    # 分页处理，每页 10 人
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    return render(request, 'communication/one_to_one_chat_selection.html', {'users': users_page})

@login_required
def task_communication_view(request, task_id):
    task = Task.objects.get(id=task_id)
    user = request.user
    if not (task.client == user or TaskApplication.objects.filter(task=task, volunteer=user, status='accepted').exists()):
        return redirect('user:home')
    room_name = f"chat_task_{task_id}"
    return render(request, 'communication/communication.html', {'room_name': room_name})

@login_required
def group_chats_view(request):
    from task.models import Task
    tasks = Task.objects.filter(status='open')  # 仅显示开放任务
    return render(request, 'communication/task_chats.html', {'tasks': tasks})

@login_required
def one_to_one_communication_view(request, room_name):
    from .models import ChatMessage, OneToOneChatSession
    # 获取聊天记录
    session = OneToOneChatSession.objects.get(room_name=room_name)
    users = [session.user1.email, session.user2.email]
    user2_email = users[0] if users[0] != request.user.email else users[1]
    messages = ChatMessage.objects.filter(
        sender__email__in=users,
        receiver__email__in=users
    ).order_by('timestamp')
    return render(request, 'communication/communication.html', {
        'room_name': room_name,
        'messages': messages,
        'user2_email': user2_email
    })

@login_required
def create_one_to_one_room(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    print("Received POST request to /communication/create-1v1-room/")  # 调试日志
    user1_email = request.user.email
    user2_email = request.POST.get('user2_email')
    print(f"User1: {user1_email}, User2: {user2_email}")  # 调试参数
    if not user2_email or user2_email == user1_email:
        return JsonResponse({'error': 'Please enter a different valid email'}, status=400)
    try:
        User = get_user_model()
        user2 = User.objects.get(email=user2_email, is_active=True)
        room_name = async_to_sync(get_or_create_one_to_one_room)(user1_email, user2_email)
        url = reverse('communication:one_to_one_communication_view', kwargs={'room_name': room_name})
        logger.info(f"Created room {room_name} for {user1_email} and {user2_email}")
        print(f"Returning JSON: {JsonResponse({'room_name': room_name, 'url': url}).content}")  # 调试返回
        return JsonResponse({'room_name': room_name, 'url': url})
    except User.DoesNotExist as e:
        logger.error(f"User {user2_email} not found or inactive: {e}")
        return JsonResponse({'error': f'User {user2_email} not found or inactive: {str(e)}'}, status=404)
    except asyncio.TimeoutError:
        logger.error("Async operation timed out")
        return JsonResponse({'error': 'Operation timed out'}, status=500)
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)