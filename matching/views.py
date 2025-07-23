from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from user.models import VolunteerProfile
from .forms import VolunteerAvailabilityForm
from django.urls import reverse
from adminpanel.models import OperationLog

# Create your views here.
@login_required
def shift(request):
    profile = request.user.userprofile.volunteerprofile

    if request.method == 'POST':
        form = VolunteerAvailabilityForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            user=request.user
            url = reverse('adminpanel:user_detail', args=[user.id])
            OperationLog.objects.create(
                user=user,
                action=f'User changed the status of shift: <a href="{url}">{user.email}</a>',
            )
            return redirect('user:home')
    else:
        form = VolunteerAvailabilityForm(instance=profile)

    return render(request, 'matching/shift.html', {'form': form})