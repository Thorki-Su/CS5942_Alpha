from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from user.models import CustomUser
from .models import ChatMessage, VideoCallSession
import logging

logger = logging.getLogger(__name__)

@login_required
def communication_view(request):
    logger.info("Entering communication_view for user: %s", request.user.email)
    room_name = f"chat_{request.user.id}_default"
    if request.user.role == 'client':
        logger.debug("User is client, searching for volunteer")
        support_worker = CustomUser.objects.filter(role='volunteer').exclude(id=request.user.id).first()
        if support_worker:
            logger.debug(f"Found volunteer: {support_worker.email} (ID: {support_worker.id})")
            room_name = f"chat_{min(request.user.id, support_worker.id)}_{max(request.user.id, support_worker.id)}"
        else:
            logger.warning("No volunteer found for client")
    else:
        logger.debug("User is volunteer, searching for client")
        client = CustomUser.objects.filter(role='client').exclude(id=request.user.id).first()
        if client:
            logger.debug(f"Found client: {client.email} (ID: {client.id})")
            room_name = f"chat_{min(request.user.id, client.id)}_{max(request.user.id, client.id)}"
        else:
            logger.warning("No client found for volunteer")
    logger.info(f"Generated room_name: {room_name} for user: {request.user.email}")
    return render(request, 'communication/communication.html', {
        'room_name': room_name,
        'user': request.user,
    })

@login_required
def task_communication_view(request, task_id):
    from task.models import Task
    task = Task.objects.get(id=task_id)
    if task.status in ['completed', 'cancelled']:
        logger.warning(f"Task {task_id} is closed, cannot join chat")
        return redirect('task:mytask')
    room_name = f"chat_task_{task.id}"
    mode = request.GET.get('mode', 'chat')  # 支持 'chat', 'audio', 'video'
    logger.info(f"Generated task room_name: {room_name} for user: {request.user.email} in mode: {mode}")
    return render(request, 'communication/communication.html', {
        'room_name': room_name,
        'user': request.user,
        'is_task_group': True,
        'mode': mode
    })

@login_required
def group_chats(request):
    from task.models import Task
    tasks = Task.objects.filter(status__in=['open', 'selected', 'ongoing']).order_by('id')
    return render(request, 'communication/group_chats.html', {'tasks': tasks})