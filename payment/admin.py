from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Donation, DonationCampaign


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'donor_display', 'amount', 'currency', 'status', 
        'is_anonymous', 'created_at', 'completed_at'
    ]
    list_filter = [
        'status', 'currency', 'is_anonymous', 'created_at', 'completed_at'
    ]
    search_fields = [
        'donor_name', 'donor_email', 'stripe_payment_intent_id', 'message'
    ]
    readonly_fields = [
        'stripe_payment_intent_id', 'stripe_charge_id', 'created_at', 
        'updated_at', 'completed_at', 'receipt_sent_at'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Donor Information', {
            'fields': ('donor', 'donor_name', 'donor_email', 'is_anonymous')
        }),
        ('Donation Details', {
            'fields': ('amount', 'currency', 'message', 'status')
        }),
        ('Payment Information', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id'),
            'classes': ('collapse',)
        }),
        ('Receipt Information', {
            'fields': ('receipt_sent', 'receipt_sent_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def donor_display(self, obj):
        """Display donor name with link to user if available"""
        if obj.donor:
            url = reverse('admin:user_customuser_change', args=[obj.donor.pk])
            return format_html('<a href="{}">{}</a>', url, obj.display_name)
        return obj.display_name
    donor_display.short_description = 'Donor'
    donor_display.admin_order_field = 'donor_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('donor')
    
    actions = ['mark_as_completed', 'resend_receipt']
    
    def mark_as_completed(self, request, queryset):
        """Mark selected donations as completed"""
        updated = queryset.filter(status='pending').update(status='completed')
        self.message_user(request, f'{updated} donations marked as completed.')
    mark_as_completed.short_description = 'Mark selected donations as completed'
    
    def resend_receipt(self, request, queryset):
        """Resend receipt for selected donations"""
        from .views import send_donation_receipt
        count = 0
        for donation in queryset.filter(status='completed'):
            try:
                send_donation_receipt(donation)
                count += 1
            except Exception as e:
                self.message_user(request, f'Error sending receipt for donation {donation.id}: {str(e)}', level='ERROR')
        
        if count > 0:
            self.message_user(request, f'{count} receipts sent successfully.')
    resend_receipt.short_description = 'Resend receipt for selected donations'


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'goal_amount', 'current_amount', 'progress_display', 
        'start_date', 'end_date', 'is_active'
    ]
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    readonly_fields = ['current_amount', 'created_at', 'progress_percentage']
    
    fieldsets = (
        ('Campaign Details', {
            'fields': ('title', 'description', 'goal_amount', 'current_amount')
        }),
        ('Campaign Period', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Statistics', {
            'fields': ('progress_percentage',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def progress_display(self, obj):
        """Display progress as a progress bar"""
        percentage = obj.progress_percentage
        color = 'success' if percentage >= 100 else 'info' if percentage >= 50 else 'warning'
        return format_html(
            '<div class="progress" style="width: 100px;">'
            '<div class="progress-bar bg-{}" role="progressbar" style="width: {}%">{:.1f}%</div>'
            '</div>',
            color, percentage, percentage
        )
    progress_display.short_description = 'Progress'
    
    actions = ['update_current_amounts']
    
    def update_current_amounts(self, request, queryset):
        """Update current amounts for selected campaigns"""
        for campaign in queryset:
            campaign.update_current_amount()
        self.message_user(request, f'{queryset.count()} campaigns updated.')
    update_current_amounts.short_description = 'Update current amounts'
