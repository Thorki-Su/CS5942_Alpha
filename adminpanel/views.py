import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from task.models import Task, TaskApplication, TaskRecord, Feedback, StarRelation
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import OperationLog
from payment.models import Donation
from .forms import AdminCreationForm
from datetime import datetime, timedelta
from django.http import HttpResponse


User = get_user_model()

def staff_required(view_func):
    """
    Access is only allowed for users with is_staff=True.
    """
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff)(view_func)

@staff_required
def admin_dashboard(request):
    today = timezone.localdate()
    client_count = User.objects.filter(role='client').count()
    volunteer_count = User.objects.filter(role='volunteer').count()
    task_count = Task.objects.count()
    today_task_count = Task.objects.filter(created_at__date=today).count()
    logs = OperationLog.objects.all().order_by('-timestamp')[:20]
    
    context = {
        'client_count': client_count,
        'volunteer_count': volunteer_count,
        'task_count': task_count,
        'today_task_count': today_task_count,
        'logs':logs,
    }
    return render(request, 'adminpanel/admin_dashboard.html', context)

@staff_required
def user_list(request):
    # users = User.objects.all().order_by('id')
    users = User.objects.filter(Q(role='client') | Q(role='volunteer')).order_by('id')
    return render(request, 'adminpanel/user_list.html', {'users': users})

@staff_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    give_stars = StarRelation.objects.filter(from_user=user)
    have_stars = StarRelation.objects.filter(to_user=user)
    if user.role == 'client':
        tasks = Task.objects.filter(client=user)
        context = {
            'user': user,
            'tasks':tasks,
            'give_stars':give_stars,
            'have_stars':have_stars,
        }
    elif user.role == 'volunteer':
        applications = TaskApplication.objects.filter(volunteer=user)
        context = {
            'user': user,
            'applications':applications,
            'give_stars':give_stars,
            'have_stars':have_stars,
        }
    else:
        context = {
            'user': user,
            'give_stars':give_stars,
            'have_stars':have_stars,
        }
    return render(request, 'adminpanel/user_detail.html', context)

@staff_required
def task_list(request):
    tasks = Task.objects.all().order_by('id')
    return render(request, 'adminpanel/task_list.html', {'tasks':tasks})

@staff_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    applications = TaskApplication.objects.filter(task=task)
    records = TaskRecord.objects.filter(task=task)
    feedbacks = Feedback.objects.filter(task=task)

    context = {
        'task': task,
        'applications': applications,
        'records':records,
        'feedbacks':feedbacks,
    }
    return render(request, 'adminpanel/task_detail.html', context)

@staff_required
def user_file(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'adminpanel/user_file.html', {'user':user})

@require_POST
@staff_required
def update_eligibility(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile

    eligibility = request.POST.get("eligibility")

    if eligibility in ["true", "false"]:
        profile.eligibility_confirmed = (eligibility == "true")
        profile.save()
        messages.success(request, f"{user.email} is updated to {eligibility}.")
    else:
        messages.error(request, "Invalid eligibility status parameter.")

    return redirect("adminpanel:user_file", user_id=user.id)

@staff_required
def records(request):
    logs = OperationLog.objects.all().order_by('-timestamp')
    return render(request, 'adminpanel/records.html', {'logs':logs})

@staff_required
def donations(request):
    donations = Donation.objects.filter(status='completed')
    return render(request, 'adminpanel/donations.html', {'donations':donations})

@staff_required
def help(request):
    return render(request, 'adminpanel/help.html')

@staff_required
def create_admin_view(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminpanel:dashboard')
    else:
        form = AdminCreationForm()
    return render(request, 'adminpanel/create_admin.html', {'form': form})

@staff_required
def export_donations_csv(request):
    """Export donation records as CSV"""
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    donations = Donation.objects.all().order_by('-created_at')
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            donations = donations.filter(created_at__gte=start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            donations = donations.filter(created_at__lte=end)
        except ValueError:
            pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=\"donations.csv\"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Email', 'Amount (GBP)', 'Message', 'Status',
        'Completed At', 'Anonymous', 'Receipt Sent'
    ])

    for donation in donations:
        writer.writerow([
            donation.id,
            donation.donor_name,
            donation.donor_email,
            donation.amount,
            donation.message or '',
            donation.status,
            donation.completed_at.strftime('%Y-%m-%d %H:%M') if donation.completed_at else '',
            'Yes' if donation.is_anonymous else 'No',
            'Yes' if donation.receipt_sent else 'No',
        ])

    return response

