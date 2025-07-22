from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Donation(models.Model):
    DONATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Donor information
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations', null=True, blank=True)
    donor_name = models.CharField(max_length=100, help_text="Name for anonymous donations")
    donor_email = models.EmailField(help_text="Email for receipt and updates")
    
    # Donation details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GBP')
    message = models.TextField(blank=True, help_text="Optional message from donor")
    is_anonymous = models.BooleanField(default=False, help_text="Hide donor name publicly")
    
    # Payment information
    stripe_payment_intent_id = models.CharField(max_length=200, unique=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=DONATION_STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Receipt information
    receipt_sent = models.BooleanField(default=False)
    receipt_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        donor_display = self.donor_name if self.donor_name else (self.donor.userprofile.get_full_name if self.donor else "Anonymous")
        return f"£{self.amount} from {donor_display} - {self.status}"
    
    @property
    def display_name(self):
        """Return the name to display publicly"""
        if self.is_anonymous:
            return "Anonymous Donor"
        return self.donor_name if self.donor_name else (self.donor.userprofile.get_full_name if self.donor else "Anonymous Donor")
    
    def mark_completed(self):
        """Mark donation as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self):
        """Mark donation as failed"""
        self.status = 'failed'
        self.save()


class DonationCampaign(models.Model):
    """Optional: For future fundraising campaigns"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.goal_amount > 0:
            return min(100, (float(self.current_amount) / float(self.goal_amount)) * 100)
        return 0
    
    def update_current_amount(self):
        """Update current amount from completed donations"""
        from django.db.models import Sum
        total = Donation.objects.filter(
            status='completed',
            created_at__gte=self.start_date,
            created_at__lte=self.end_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        self.current_amount = total
        self.save()
