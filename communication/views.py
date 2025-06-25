from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from user.models import CustomUser
from .models import ChatMessage, VideoCallSession
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)

@login_required
def communication_view(request):
    """
    处理通信视图，生成 room_name 并渲染聊天界面。
    """
    logger.info("Entering communication_view for user: %s", request.user.email)
    
    # 默认 room_name
    room_name = f"{request.user.id}_default"
    
    # 根据角色匹配其他用户
    if request.user.role == 'client':
        logger.debug("User is client, searching for volunteer")
        support_worker = CustomUser.objects.filter(role='volunteer').exclude(id=request.user.id).first()
        if support_worker:
            logger.debug(f"Found volunteer: {support_worker.email} (ID: {support_worker.id})")
            room_name = f"{min(request.user.id, support_worker.id)}_{max(request.user.id, support_worker.id)}"
        else:
            logger.warning("No volunteer found for client")
    else:  # volunteer
        logger.debug("User is volunteer, searching for client")
        client = CustomUser.objects.filter(role='client').exclude(id=request.user.id).first()
        if client:
            logger.debug(f"Found client: {client.email} (ID: {client.id})")
            room_name = f"{min(request.user.id, client.id)}_{max(request.user.id, client.id)}"
        else:
            logger.warning("No client found for volunteer")

    logger.info(f"Generated room_name: {room_name} for user: {request.user.email}")
    return render(request, 'communication/communication.html', {
        'room_name': room_name,
        'user': request.user
    })

@login_required
def start_video_call(request):
    """
    处理视频通话请求，创建会话并渲染视频通话界面。
    """
    logger.info("Entering start_video_call for user: %s", request.user.email)
    if request.method == 'POST':
        participant_id = request.POST.get('participant_id')
        try:
            participant = CustomUser.objects.get(id=participant_id)
            logger.debug(f"Found participant: {participant.email} (ID: {participant.id})")
            session = VideoCallSession.objects.create(initiator=request.user, participant=participant)
            room_name = f"{min(request.user.id, participant.id)}_{max(request.user.id, participant.id)}"
            logger.info(f"Video call room_name: {room_name}")
            return render(request, 'communication/video_call.html', {
                'room_name': room_name,
                'participant': participant
            })
        except CustomUser.DoesNotExist:
            logger.error(f"Participant with ID {participant_id} not found")
            return render(request, 'communication/video_call.html', {'error': 'Participant not found'})
    logger.warning("Invalid request method for start_video_call")
    return render(request, 'communication/video_call.html')