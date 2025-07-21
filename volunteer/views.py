from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .utils import calculate_volunteer_duration, format_volunteer_duration
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import os


@login_required
def service_certificate(request):
    """
    Display the volunteer service certificate page.
    """
    if request.user.role != 'volunteer':
        messages.error(request, 'Access denied. Only volunteers can view certificates.')
        return redirect('user:profile_detail')
    
    total_hours = calculate_volunteer_duration(request.user)
    formatted_duration = format_volunteer_duration(total_hours)
    
    if total_hours == 0:
        messages.info(request, 'Complete your first volunteer task to generate a service certificate.')
        return redirect('user:profile_detail')
    
    context = {
        'user': request.user,
        'user_profile': request.user.userprofile,
        'total_hours': total_hours,
        'formatted_duration': formatted_duration,
        'current_date': timezone.now().strftime('%B %d, %Y'),
    }
    
    return render(request, 'volunteer/service_certificate.html', context)


@login_required
def download_certificate(request):
    """
    Generate and download the volunteer service certificate as PDF.
    """
    if request.user.role != 'volunteer':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    total_hours = calculate_volunteer_duration(request.user)
    
    if total_hours == 0:
        return JsonResponse({'error': 'No volunteer hours recorded'}, status=400)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#2E8B57')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=HexColor('#4682B4')
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        alignment=TA_CENTER,
        leading=18
    )
    
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=HexColor('#666666')
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph("VOLUNTEER SERVICE CERTIFICATE", title_style))
    story.append(Spacer(1, 20))
    
    # Subtitle
    story.append(Paragraph("Certificate of Appreciation", subtitle_style))
    story.append(Spacer(1, 30))
    
    # Main content
    user_name = request.user.userprofile.get_full_name
    formatted_duration = format_volunteer_duration(total_hours)
    current_date = timezone.now().strftime('%B %d, %Y')
    
    story.append(Paragraph("This is to certify that", body_style))
    story.append(Spacer(1, 10))
    
    name_style = ParagraphStyle(
        'Name',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=HexColor('#2E8B57'),
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph(f"<u>{user_name}</u>", name_style))
    
    story.append(Paragraph("has successfully completed volunteer service with", body_style))
    story.append(Paragraph("<b>Shallion Support</b>", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph(f"Total Service Hours: <b>{formatted_duration}</b>", body_style))
    story.append(Paragraph(f"({total_hours:.1f} hours)", body_style))
    story.append(Spacer(1, 30))
    
    story.append(Paragraph("We deeply appreciate your dedication, compassion, and commitment", body_style))
    story.append(Paragraph("to supporting our community members in need.", body_style))
    story.append(Paragraph("Your volunteer service has made a meaningful difference", body_style))
    story.append(Paragraph("in the lives of those you have helped.", body_style))
    story.append(Spacer(1, 40))
    
    story.append(Paragraph("Thank you for your invaluable contribution to our mission", body_style))
    story.append(Paragraph("of building a stronger, more supportive community.", body_style))
    story.append(Spacer(1, 50))
    
    # Date and authorization
    story.append(Paragraph(f"Issued on: {current_date}", signature_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Authorized by: <b>Shallion Support</b>", signature_style))
    story.append(Paragraph("Community Volunteer Program", signature_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    filename = f"volunteer_certificate_{request.user.userprofile.first_name}_{request.user.userprofile.last_name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


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
