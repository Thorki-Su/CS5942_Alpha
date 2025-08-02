from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import mail
from django.conf import settings
from unittest.mock import patch, Mock, MagicMock
from decimal import Decimal
import json
import stripe

from .models import Donation, DonationCampaign
from .forms import DonationForm
from user.models import UserProfile

User = get_user_model()


class DonationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='donor@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            phone_number='1234567890',
            location='AB12 3CD'
        )
        self.donation = Donation.objects.create(
            donor=self.user,
            donor_name='John Doe',
            donor_email='donor@test.com',
            amount=Decimal('50.00'),
            message='Test donation',
            stripe_payment_intent_id='pi_test123',
            status='pending'
        )

    def test_donation_creation(self):
        """Test donation record creation"""
        self.assertEqual(self.donation.donor, self.user)
        self.assertEqual(self.donation.donor_name, 'John Doe')
        self.assertEqual(self.donation.donor_email, 'donor@test.com')
        self.assertEqual(self.donation.amount, Decimal('50.00'))
        self.assertEqual(self.donation.currency, 'GBP')
        self.assertEqual(self.donation.status, 'pending')
        self.assertFalse(self.donation.is_anonymous)
        self.assertFalse(self.donation.receipt_sent)

    def test_donation_str_method(self):
        """Test donation record string representation"""
        expected = "£50.00 from John Doe - pending"
        self.assertEqual(str(self.donation), expected)

    def test_donation_display_name_normal(self):
        """Test normal donor display name"""
        self.assertEqual(self.donation.display_name, 'John Doe')

    def test_donation_display_name_anonymous(self):
        """Test anonymous donor display name"""
        self.donation.is_anonymous = True
        self.assertEqual(self.donation.display_name, 'Anonymous Donor')

    def test_donation_display_name_no_donor_name(self):
        """Test display name when donor name is empty"""
        self.donation.donor_name = ''
        self.assertEqual(self.donation.display_name, 'John Doe')  # 从用户资料获取

    def test_donation_display_name_no_donor_user(self):
        """Test display name when no associated user"""
        donation = Donation.objects.create(
            donor_name='Anonymous',
            donor_email='anon@test.com',
            amount=Decimal('25.00'),
            stripe_payment_intent_id='pi_test456',
            status='pending'
        )
        self.assertEqual(donation.display_name, 'Anonymous')

    def test_mark_completed(self):
        """Test marking donation as completed"""
        self.assertIsNone(self.donation.completed_at)
        self.donation.mark_completed()
        
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'completed')
        self.assertIsNotNone(self.donation.completed_at)

    def test_mark_failed(self):
        """Test marking donation as failed"""
        self.donation.mark_failed()
        
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'failed')

    # def test_donation_ordering(self):
    #     """Test donation records ordered by creation time descending"""
    #     donation2 = Donation.objects.create(
    #         donor_name='Jane Doe',
    #         donor_email='jane@test.com',
    #         amount=Decimal('100.00'),
    #         stripe_payment_intent_id='pi_test789',
    #         status='completed'
    #     )
        
    #     donations = list(Donation.objects.all())
    #     self.assertEqual(donations[0], donation2)  # Latest first
    #     self.assertEqual(donations[1], self.donation)


class DonationCampaignModelTests(TestCase):
    def setUp(self):
        self.campaign = DonationCampaign.objects.create(
            title='Test Campaign',
            description='Test campaign description',
            goal_amount=Decimal('1000.00'),
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=30),
            is_active=True
        )

    def test_campaign_creation(self):
        """Test donation campaign creation"""
        self.assertEqual(self.campaign.title, 'Test Campaign')
        self.assertEqual(self.campaign.goal_amount, Decimal('1000.00'))
        self.assertEqual(self.campaign.current_amount, Decimal('0.00'))
        self.assertTrue(self.campaign.is_active)

    def test_campaign_str_method(self):
        """Test donation campaign string representation"""
        self.assertEqual(str(self.campaign), 'Test Campaign')

    def test_progress_percentage_zero(self):
        """Test progress percentage when zero"""
        self.assertEqual(self.campaign.progress_percentage, 0)

    def test_progress_percentage_partial(self):
        """Test partial completion progress percentage"""
        self.campaign.current_amount = Decimal('250.00')
        self.assertEqual(self.campaign.progress_percentage, 25.0)

    def test_progress_percentage_complete(self):
        """Test progress percentage when complete"""
        self.campaign.current_amount = Decimal('1000.00')
        self.assertEqual(self.campaign.progress_percentage, 100.0)

    def test_progress_percentage_over_goal(self):
        """Test progress percentage when over goal"""
        self.campaign.current_amount = Decimal('1500.00')
        self.assertEqual(self.campaign.progress_percentage, 100.0)  # Maximum 100%

    def test_update_current_amount(self):
        """Test updating current amount"""
        # Create some completed donations
        Donation.objects.create(
            donor_name='Donor 1',
            donor_email='donor1@test.com',
            amount=Decimal('100.00'),
            stripe_payment_intent_id='pi_test1',
            status='completed',
            completed_at=timezone.now()
        )
        Donation.objects.create(
            donor_name='Donor 2',
            donor_email='donor2@test.com',
            amount=Decimal('150.00'),
            stripe_payment_intent_id='pi_test2',
            status='completed',
            completed_at=timezone.now()
        )
        # Create an incomplete donation (should not be counted)
        Donation.objects.create(
            donor_name='Donor 3',
            donor_email='donor3@test.com',
            amount=Decimal('200.00'),
            stripe_payment_intent_id='pi_test3',
            status='pending'
        )
        
        self.campaign.update_current_amount()
        self.assertEqual(self.campaign.current_amount, Decimal('250.00'))


class DonationFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            phone_number='1234567890',
            location='AB12 3CD'
        )

    def test_form_with_preset_amount(self):
        """Test form with preset amount"""
        form_data = {
            'amount_choice': '50',
            'donor_name': 'John Doe',
            'donor_email': 'john@test.com',
            'message': 'Test donation',
            'is_anonymous': False
        }
        form = DonationForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], 50.0)

    def test_form_with_custom_amount(self):
        """Test form with custom amount"""
        form_data = {
            'amount_choice': 'custom',
            'custom_amount': '75.50',
            'donor_name': 'Jane Doe',
            'donor_email': 'jane@test.com',
            'message': 'Custom donation',
            'is_anonymous': True
        }
        form = DonationForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('75.50'))

    def test_form_custom_amount_missing(self):
        """Test custom amount selected but not filled"""
        form_data = {
            'amount_choice': 'custom',
            'donor_name': 'John Doe',
            'donor_email': 'john@test.com'
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Please enter a custom amount.', form.non_field_errors())

    def test_form_no_amount_selected(self):
        """Test no amount selected"""
        form_data = {
            'donor_name': 'John Doe',
            'donor_email': 'john@test.com'
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Please select a donation amount.', form.non_field_errors())

    def test_form_missing_donor_name(self):
        """Test missing donor name"""
        form_data = {
            'amount_choice': '25',
            'donor_email': 'john@test.com'
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Please enter your name.', form.non_field_errors())

    def test_form_missing_donor_email(self):
        """Test missing donor email"""
        form_data = {
            'amount_choice': '25',
            'donor_name': 'John Doe'
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Please enter your email address.', form.non_field_errors())

    def test_form_prefill_authenticated_user(self):
        """Test form prefill for authenticated user"""
        form = DonationForm(user=self.user)
        self.assertEqual(form.fields['donor_name'].initial, 'Test User')
        self.assertEqual(form.fields['donor_email'].initial, 'user@test.com')

    def test_form_prefill_unauthenticated_user(self):
        """Test form for unauthenticated user"""
        form = DonationForm(user=None)
        self.assertIsNone(form.fields['donor_name'].initial)
        self.assertIsNone(form.fields['donor_email'].initial)

    def test_custom_amount_validation_min(self):
        """Test custom amount minimum value validation"""
        form_data = {
            'amount_choice': 'custom',
            'custom_amount': '0.50',  # Below minimum value 1
            'donor_name': 'John Doe',
            'donor_email': 'john@test.com'
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('custom_amount', form.errors)

    def test_custom_amount_validation_max(self):
        """Test custom amount maximum value validation"""
        form_data = {
            'amount_choice': 'custom',
            'custom_amount': '15000.00',  # Above maximum value 10000
            'donor_name': 'John Doe',
            'donor_email': 'john@test.com'
        }
        form = DonationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('custom_amount', form.errors)


class DonationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            phone_number='1234567890',
            location='AB12 3CD'
        )
        # Create some test donations
        self.completed_donation = Donation.objects.create(
            donor=self.user,
            donor_name='Test User',
            donor_email='user@test.com',
            amount=Decimal('100.00'),
            stripe_payment_intent_id='pi_completed',
            status='completed',
            completed_at=timezone.now()
        )

    def test_donation_page_get(self):
        """Test donation page GET request"""
        response = self.client.get(reverse('payment:donation_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/donation_page.html')
        self.assertIn('form', response.context)
        self.assertIn('recent_donations', response.context)
        self.assertIn('total_donated', response.context)
        self.assertIn('total_donors', response.context)

    def test_donation_page_statistics(self):
        """Test donation page statistics"""
        response = self.client.get(reverse('payment:donation_page'))
        self.assertEqual(response.context['total_donated'], Decimal('100.00'))
        self.assertEqual(response.context['total_donors'], 1)

    # @patch('stripe.PaymentIntent.create')
    # def test_donation_page_post_success(self, mock_stripe_create):
    #     """Test successful donation POST request"""
    #     mock_payment_intent = Mock()
    #     mock_payment_intent.id = 'pi_test123'
    #     mock_payment_intent.client_secret = 'pi_test123_secret'
    #     mock_stripe_create.return_value = mock_payment_intent

    #     form_data = {
    #         'amount_choice': '50',
    #         'donor_name': 'John Doe',
    #         'donor_email': 'john@test.com',
    #         'message': 'Test donation',
    #         'is_anonymous': False
    #     }
        
    #     response = self.client.post(
    #         reverse('payment:donation_page'),
    #         data=form_data,
    #         content_type='application/x-www-form-urlencoded'
    #     )
        
    #     self.assertEqual(response.status_code, 200)
    #     data = response.json()
    #     self.assertTrue(data['success'])
    #     self.assertEqual(data['client_secret'], 'pi_test123_secret')
    #     self.assertIn('donation_id', data)
        
    #     # Verify donation record created
    #     donation = Donation.objects.get(stripe_payment_intent_id='pi_test123')
    #     self.assertEqual(donation.amount, Decimal('50.00'))
    #     self.assertEqual(donation.donor_name, 'John Doe')

    @patch('stripe.PaymentIntent.create')
    def test_donation_page_post_stripe_error(self, mock_stripe_create):
        """Test Stripe error handling"""
        mock_stripe_create.side_effect = stripe.error.StripeError("Test error")

        form_data = {
            'amount_choice': '50',
            'donor_name': 'John Doe',
            'donor_email': 'john@test.com'
        }
        
        response = self.client.post(
            reverse('payment:donation_page'),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Payment processing error. Please try again.')

    def test_donation_page_post_invalid_form(self):
        """Test invalid form handling"""
        form_data = {
            'amount_choice': '50',
            # Missing required fields
        }
        
        response = self.client.post(
            reverse('payment:donation_page'),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('errors', data)

    @patch('stripe.PaymentIntent.retrieve')
    def test_donation_success_view(self, mock_stripe_retrieve):
        """Test donation success page"""
        mock_payment_intent = Mock()
        mock_payment_intent.status = 'succeeded'
        mock_stripe_retrieve.return_value = mock_payment_intent

        donation = Donation.objects.create(
            donor_name='Test Donor',
            donor_email='test@test.com',
            amount=Decimal('75.00'),
            stripe_payment_intent_id='pi_success_test',
            status='pending'
        )
        
        response = self.client.get(
            reverse('payment:donation_success', args=[donation.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/donation_success.html')
        self.assertEqual(response.context['donation'], donation)
        
        # Verify donation status updated
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'completed')

    def test_donation_cancel_view(self):
        """Test donation cancel page"""
        response = self.client.get(reverse('payment:donation_cancel'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/donation_cancel.html')

    def test_donation_list_view(self):
        """Test donation list page"""
        response = self.client.get(reverse('payment:donation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/donation_list.html')
        self.assertIn('donations', response.context)
        self.assertIn('total_donated', response.context)
        self.assertIn('total_donors', response.context)
        
        # Verify only completed donations are shown
        donations = response.context['donations']
        for donation in donations:
            self.assertEqual(donation.status, 'completed')


class StripeWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.donation = Donation.objects.create(
            donor_name='Test Donor',
            donor_email='test@test.com',
            amount=Decimal('50.00'),
            stripe_payment_intent_id='pi_webhook_test',
            status='pending'
        )

    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_succeeded(self, mock_construct_event):
        """Test payment succeeded webhook"""
        mock_event = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_webhook_test',
                    'latest_charge': 'ch_test123'
                }
            }
        }
        mock_construct_event.return_value = mock_event

        response = self.client.post(
            reverse('payment:stripe_webhook'),
            data='test_payload',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify donation status updated
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'completed')
        self.assertEqual(self.donation.stripe_charge_id, 'ch_test123')

    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_failed(self, mock_construct_event):
        """Test payment failed webhook"""
        mock_event = {
            'type': 'payment_intent.payment_failed',
            'data': {
                'object': {
                    'id': 'pi_webhook_test'
                }
            }
        }
        mock_construct_event.return_value = mock_event

        response = self.client.post(
            reverse('payment:stripe_webhook'),
            data='test_payload',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify donation status updated
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, 'failed')

    @patch('stripe.Webhook.construct_event')
    def test_webhook_invalid_signature(self, mock_construct_event):
        """Test webhook with invalid signature"""
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "test_signature"
        )

        response = self.client.post(
            reverse('payment:stripe_webhook'),
            data='test_payload',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        self.assertEqual(response.status_code, 400)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_invalid_payload(self, mock_construct_event):
        """Test webhook with invalid payload"""
        mock_construct_event.side_effect = ValueError("Invalid payload")

        response = self.client.post(
            reverse('payment:stripe_webhook'),
            data='invalid_payload',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, 400)

    def test_webhook_donation_not_found(self):
        """Test webhook when donation record not found"""
        with patch('stripe.Webhook.construct_event') as mock_construct_event:
            mock_event = {
                'type': 'payment_intent.succeeded',
                'data': {
                    'object': {
                        'id': 'pi_nonexistent',
                        'latest_charge': 'ch_test123'
                    }
                }
            }
            mock_construct_event.return_value = mock_event

            response = self.client.post(
                reverse('payment:stripe_webhook'),
                data='test_payload',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='test_signature'
            )
            
            self.assertEqual(response.status_code, 200)  # webhook still returns 200


class EmailTests(TestCase):
    def setUp(self):
        self.donation = Donation.objects.create(
            donor_name='Test Donor',
            donor_email='test@test.com',
            amount=Decimal('100.00'),
            stripe_payment_intent_id='pi_email_test',
            status='completed',
            completed_at=timezone.now()
        )

    def test_send_donation_receipt(self):
        """Test sending donation receipt email"""
        from payment.views import send_donation_receipt
        
        # Clear email outbox
        mail.outbox = []
        
        send_donation_receipt(self.donation)
        
        # Verify email sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Thank you for your donation', email.subject)
        self.assertEqual(email.to, ['test@test.com'])
        self.assertIn('£100.00', email.body)
        
        # Verify receipt status updated
        self.donation.refresh_from_db()
        self.assertTrue(self.donation.receipt_sent)
        self.assertIsNotNone(self.donation.receipt_sent_at)

    def test_send_donation_receipt_already_sent(self):
        """Test not sending receipt twice"""
        from payment.views import send_donation_receipt
        
        # Mark receipt as sent
        self.donation.receipt_sent = True
        self.donation.save()
        
        mail.outbox = []
        send_donation_receipt(self.donation)
        
        # Verify no email sent
        self.assertEqual(len(mail.outbox), 0)

    @patch('payment.views.send_mail')
    def test_send_donation_receipt_email_error(self, mock_send_mail):
        """Test email sending error handling"""
        from payment.views import send_donation_receipt
        
        mock_send_mail.side_effect = Exception("Email sending failed")
        
        # Should not raise exception
        send_donation_receipt(self.donation)
        
        # Receipt status should not be updated
        self.donation.refresh_from_db()
        self.assertFalse(self.donation.receipt_sent)


class IntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='integration@test.com',
            password='testpass123',
            role='client',
            is_active=True
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Integration',
            last_name='Test',
            phone_number='1234567890',
            location='AB12 3CD'
        )

    @patch('stripe.PaymentIntent.create')
    @patch('stripe.PaymentIntent.retrieve')
    def test_complete_donation_flow(self, mock_stripe_retrieve, mock_stripe_create):
        """Test complete donation flow"""
        # Mock Stripe responses
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_integration_test'
        mock_payment_intent.client_secret = 'pi_integration_test_secret'
        mock_payment_intent.status = 'succeeded'
        mock_payment_intent.latest_charge = 'ch_integration_test'
        
        mock_stripe_create.return_value = mock_payment_intent
        mock_stripe_retrieve.return_value = mock_payment_intent

        # 1. Visit donation page
        response = self.client.get(reverse('payment:donation_page'))
        self.assertEqual(response.status_code, 200)

        # 2. Submit donation form
        form_data = {
            'amount_choice': '100',
            'donor_name': 'Integration Test',
            'donor_email': 'integration@test.com',
            'message': 'Integration test donation',
            'is_anonymous': False
        }
        
        response = self.client.post(
            reverse('payment:donation_page'),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # 3. Get created donation record
        donation = Donation.objects.get(stripe_payment_intent_id='pi_integration_test')
        self.assertEqual(donation.amount, Decimal('100.00'))
        self.assertEqual(donation.status, 'pending')

        # 4. Visit success page (simulate payment success)
        response = self.client.get(
            reverse('payment:donation_success', args=[donation.id])
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify donation status updated
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'completed')

        # 5. Verify donation appears in public list
        response = self.client.get(reverse('payment:donation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Test')
        self.assertContains(response, '£100.00')

    def test_anonymous_donation_privacy(self):
        """Test anonymous donation privacy protection"""
        # Create anonymous donation
        donation = Donation.objects.create(
            donor_name='Secret Donor',
            donor_email='secret@test.com',
            amount=Decimal('50.00'),
            stripe_payment_intent_id='pi_anonymous_test',
            status='completed',
            completed_at=timezone.now(),
            is_anonymous=True
        )

        # Visit donation list
        response = self.client.get(reverse('payment:donation_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verify anonymous donation shows as "Anonymous Donor"
        self.assertContains(response, 'Anonymous Donor')
        self.assertNotContains(response, 'Secret Donor')