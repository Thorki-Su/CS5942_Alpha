from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Sum


import stripe
import json
import logging

from .models import Donation, DonationCampaign
from .forms import DonationForm

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

logger = logging.getLogger(__name__)

def donation_page(request):
    """Main donation page"""
    if request.method == 'POST':
        form = DonationForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                donation = form.save(commit=False)
                donation.amount = form.cleaned_data['amount']
                if request.user.is_authenticated:
                    donation.donor = request.user

                payment_intent = stripe.PaymentIntent.create(
                    amount=int(donation.amount * 100),
                    currency='gbp',
                    metadata={
                        'donor_name': donation.donor_name,
                        'donor_email': donation.donor_email,
                        'message': donation.message[:500] if donation.message else '',
                    }
                )

                donation.stripe_payment_intent_id = payment_intent.id
                donation.save()

                return JsonResponse({
                    'success': True,
                    'client_secret': payment_intent.client_secret,
                    'donation_id': donation.id
                })

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error: {str(e)}")
                return JsonResponse({'success': False, 'error': 'Payment processing error. Please try again.'})
            except Exception as e:
                logger.error(f"Donation creation error: {str(e)}")
                return JsonResponse({'success': False, 'error': 'An error occurred. Please try again.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = DonationForm(user=request.user)

    recent_donations = Donation.objects.filter(status='completed', is_anonymous=False).order_by('-completed_at')[:10]
    total_donated = Donation.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    total_donors = Donation.objects.filter(status='completed').values('donor_email').distinct().count()

    context = {
        'form': form,
        'recent_donations': recent_donations,
        'total_donated': total_donated,
        'total_donors': total_donors,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'payment/donation_page.html', context)

def donation_success(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id)
    try:
        payment_intent = stripe.PaymentIntent.retrieve(donation.stripe_payment_intent_id)
        if payment_intent.status == 'succeeded' and donation.status != 'completed':
            donation.mark_completed()
            send_donation_receipt(donation)
    except stripe.error.StripeError as e:
        logger.error(f"Error verifying payment: {str(e)}")

    return render(request, 'payment/donation_success.html', {'donation': donation})

def donation_cancel(request):
    return render(request, 'payment/donation_cancel.html')

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return HttpResponse(status=400)

    event_type = event['type']
    payment_intent = event['data']['object']

    if event_type == 'payment_intent.succeeded':
        handle_successful_payment(payment_intent)
    elif event_type == 'payment_intent.payment_failed':
        handle_failed_payment(payment_intent)
    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")

    return HttpResponse(status=200)

def handle_successful_payment(payment_intent):
    try:
        donation = Donation.objects.get(stripe_payment_intent_id=payment_intent['id'])
        if donation.status != 'completed':
            donation.stripe_charge_id = payment_intent.get('latest_charge', '')
            donation.mark_completed()
            send_donation_receipt(donation)
            logger.info(f"Donation {donation.id} marked as completed")
    except Donation.DoesNotExist:
        logger.error(f"Donation not found for payment_intent: {payment_intent['id']}")

def handle_failed_payment(payment_intent):
    try:
        donation = Donation.objects.get(stripe_payment_intent_id=payment_intent['id'])
        donation.mark_failed()
        logger.info(f"Donation {donation.id} marked as failed")
    except Donation.DoesNotExist:
        logger.error(f"Donation not found for failed payment_intent: {payment_intent['id']}")

def send_donation_receipt(donation):
    if donation.receipt_sent:
        return

    try:
        subject = f"Thank you for your donation to Shallion Support - £{donation.amount}"
        html_message = render_to_string('payment/emails/donation_receipt.html', {'donation': donation})
        plain_message = render_to_string('payment/emails/donation_receipt.txt', {'donation': donation})

        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@shallion.org'),
            [donation.donor_email],
            html_message=html_message,
            fail_silently=False,
        )

        donation.receipt_sent = True
        donation.receipt_sent_at = timezone.now()
        donation.save()
        logger.info(f"Receipt sent for donation {donation.id}")

    except Exception as e:
        logger.error(f"Error sending receipt for donation {donation.id}: {str(e)}")

def donation_list(request):
    donations = Donation.objects.filter(status='completed').order_by('-completed_at')
    total_donated = donations.aggregate(Sum('amount'))['amount__sum'] or 0
    total_donors = donations.values('donor_email').distinct().count()

    context = {
        'donations': donations,
        'total_donated': total_donated,
        'total_donors': total_donors,
    }
    return render(request, 'payment/donation_list.html', context)





