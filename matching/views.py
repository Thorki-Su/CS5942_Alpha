from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from user.models import VolunteerProfile
from .forms import VolunteerAvailabilityForm

# Create your views here.
@login_required
def shift(request):
    profile = request.user.userprofile.volunteerprofile

    if request.method == 'POST':
        form = VolunteerAvailabilityForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('matching:shift')  # 可跳转到自己定义的“成功提示页”或原页
    else:
        form = VolunteerAvailabilityForm(instance=profile)

    return render(request, 'matching/shift.html', {'form': form})