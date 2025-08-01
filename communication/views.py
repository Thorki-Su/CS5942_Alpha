import time
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from task.models import Task, TaskApplication
from .models import OneToOneChatSession, ChatMessage
from asgiref.sync import sync_to_async, async_to_sync
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count
import asyncio
import logging

logger = logging.getLogger(__name__)

@sync_to_async
def get_or_create_one_to_one_room(user1_email, user2_email):
    start_time = time.time()
    try:
        User = get_user_model()
        user1 = User.objects.get(email=user1_email, is_active=True)
        user2 = User.objects.get(email=user2_email, is_active=True)
        users = sorted([user1, user2], key=lambda x: x.id)
        user1, user2 = users[0], users[1]
        room_name = f"1v1_{user1.id}_{user2.id}"
        existing_sessions = OneToOneChatSession.objects.filter(user1=user1, user2=user2)
        if existing_sessions.exists():
            logger.debug(f"Found existing session {room_name} in {time.time() - start_time:.3f}s")
            return existing_sessions[0].room_name
        session, created = OneToOneChatSession.objects.get_or_create(
            user1=user1,
            user2=user2,
            defaults={'room_name': room_name}
        )
        logger.debug(f"{'Created' if created else 'Retrieved'} session {room_name} in {time.time() - start_time:.3f}s")
        return session.room_name
    except User.DoesNotExist as e:
        logger.error(f"User not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in get_or_create_one_to_one_room: {e}")
        raise

@login_required
def message_selection_view(request):
    user = request.user
    one_to_one_unread = ChatMessage.objects.filter(
        receiver=user, is_group=False, is_read=False
    ).count()
    task_unread = ChatMessage.objects.filter(
        is_group=True, is_read=False,
        task__in=Task.objects.filter(
            Q(client=user) | Q(applications__volunteer=user, applications__status='accepted')
        )
    ).count()
    logger.debug(f"Queried unread counts: 1v1={one_to_one_unread}, task={task_unread}")
    return render(request, 'communication/message_selection.html', {
        'one_to_one_unread': one_to_one_unread,
        'task_unread': task_unread
    })

@login_required
def one_to_one_chat_selection_view(request):
    start_time = time.time()
    User = get_user_model()
    search_query = request.GET.get('q', '').strip()
    users = User.objects.exclude(email=request.user.email).filter(is_active=True).order_by('id')
    if search_query:
        users = users.filter(email__icontains=search_query)
    
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    logger.debug(f"Queried users for one_to_one_chat_selection in {time.time() - start_time:.3f}s")
    return render(request, 'communication/one_to_one_chat_selection.html', {'users': users_page})

@login_required
def task_communication_view(request, task_id):
    start_time = time.time()
    try:
        task = Task.objects.get(id=task_id)
        if not (task.client == request.user or TaskApplication.objects.filter(
                task=task, volunteer=request.user, status='accepted').exists()):
            logger.warning(f"User {request.user.email} unauthorized for task {task_id}")
            return redirect('user:home')
        if task.status in ['completed', 'cancelled']:
            logger.warning(f"Task {task_id} is {task.status}")
            return redirect('user:home')
        room_name = f"chat_task_{task_id}"
        participants = [task.client.email] + list(TaskApplication.objects.filter(
            task=task, status='accepted').values_list('volunteer__email', flat=True))
        messages = ChatMessage.objects.filter(task=task).order_by('timestamp')
        # Mark task messages as read
        ChatMessage.objects.filter(
            task=task, is_group=True, is_read=False
        ).update(is_read=True)
        logger.debug(f"Loaded task communication view for task {task_id} in {time.time() - start_time:.3f}s")
        return render(request, 'communication/communication.html', {
            'room_name': room_name,
            'messages': messages,
            'user2_email': 'Task Group Chat',
            'participants': participants
        })
    except Task.DoesNotExist:
        logger.error(f"Task {task_id} not found")
        return redirect('user:home')

@login_required
def group_chats_view(request):
    start_time = time.time()
    tasks = Task.objects.filter(status='open')
    logger.debug(f"Loaded group chats view in {time.time() - start_time:.3f}s")
    return render(request, 'communication/task_chats.html', {'tasks': tasks})

@login_required
def one_to_one_communication_view(request, room_name):
    start_time = time.time()
    try:
        session = OneToOneChatSession.objects.get(room_name=room_name)
        if request.user not in [session.user1, session.user2]:
            logger.warning(f"User {request.user.email} unauthorized for room {room_name}")
            return redirect('user:home')
    except OneToOneChatSession.DoesNotExist:
        logger.error(f"OneToOneChatSession {room_name} not found")
        return redirect('communication:one_to_one_chat_selection')
    users = [session.user1.email, session.user2.email]
    user2_email = users[0] if users[0] != request.user.email else users[1]
    messages = ChatMessage.objects.filter(
        sender__email__in=users,
        receiver__email__in=users
    ).order_by('timestamp')
    # Mark 1v1 messages as read
    ChatMessage.objects.filter(
        receiver=request.user, is_group=False, is_read=False,
        sender__email=user2_email
    ).update(is_read=True)
    logger.debug(f"Loaded one-to-one communication view for room {room_name} in {time.time() - start_time:.3f}s")
    return render(request, 'communication/communication.html', {
        'room_name': room_name,
        'messages': messages,
        'user2_email': user2_email,
        'participants': [request.user.email, user2_email]
    })

@login_required
def create_one_to_one_room(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    user1_email = request.user.email
    user2_email = request.POST.get('user2_email')
    if not user2_email or user2_email == user1_email:
        return JsonResponse({'error': 'Please enter a different valid email'}, status=400)
    try:
        start_time = time.time()
        room_name = async_to_sync(get_or_create_one_to_one_room)(user1_email, user2_email)
        url = reverse('communication:one_to_one_communication_view', kwargs={'room_name': room_name})
        logger.info(f"Created room {room_name} for {user1_email} and {user2_email} in {time.time() - start_time:.3f}s")
        return JsonResponse({'room_name': room_name, 'url': url})
    except get_user_model().DoesNotExist as e:
        logger.error(f"User {user2_email} not found or inactive: {e}")
        return JsonResponse({'error': f'User {user2_email} not found or inactive: {str(e)}'}, status=404)
    except asyncio.TimeoutError:
        logger.error("Async operation timed out")
        return JsonResponse({'error': 'Operation timed out'}, status=500)
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_unread_details(request):
    user = request.user
    one_to_one_unread = ChatMessage.objects.filter(
        receiver=user, is_group=False, is_read=False
    ).values('sender__email').annotate(count=Count('id'))
    task_unread = ChatMessage.objects.filter(
        is_group=True, is_read=False,
        task__in=Task.objects.filter(
            Q(client=user) | Q(applications__volunteer=user, applications__status='accepted')
        )
    ).values('task__id', 'task__title').annotate(count=Count('id'))
    return JsonResponse({
        'one_to_one': list(one_to_one_unread),
        'task': list(task_unread)
    })