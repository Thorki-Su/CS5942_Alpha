from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .utils import calculate_volunteer_duration, format_volunteer_duration


@login_required
def get_volunteer_stats(request):
    """
    API endpoint to get volunteer statistics including duration.
    Can be used for AJAX requests or future features.
    """
    if request.user.role != 'volunteer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    total_hours = calculate_volunteer_duration(request.user)
    formatted_duration = format_volunteer_duration(total_hours)
    
    return JsonResponse({
        'total_hours': total_hours,
        'formatted_duration': formatted_duration,
        'status': 'success'
    })
