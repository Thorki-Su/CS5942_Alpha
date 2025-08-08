# user/utils.py

import requests
import re
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.conf import settings

def normalize_uk_postcode(postcode):
    postcode = postcode.upper().strip().replace(' ', '')
    # Insert space to standard format, e.g. AB253DD -> AB25 3DD
    return re.sub(r'([A-Z]{1,2}\d{1,2})(\d[A-Z]{2})', r'\1 \2', postcode)

def is_valid_aberdeen_postcode(postcode):
    postcode = normalize_uk_postcode(postcode)
    resp_validate = requests.get(f'https://api.postcodes.io/postcodes/{postcode}/validate')
    if resp_validate.status_code != 200 or not resp_validate.json().get('result', False):
        return False

    resp_lookup = requests.get(f'https://api.postcodes.io/postcodes/{postcode}')
    if resp_lookup.status_code != 200:
        return False

    data = resp_lookup.json().get('result')
    if not data:
        return False

    district = data.get('admin_district', '').lower()
    if 'aberdeen' in district:
        return True
    return False

def geocode_address(address):
    # Filter out invalid segments like null in address first
    clean_parts = [part.strip() for part in str(address).split(',') if part and part.lower() != 'null']
    
    # Add country for safety
    cleaned_address = ', '.join(clean_parts + ['UK'])

    # print(f"Attempting to parse address: {cleaned_address}")

    url = f"https://nominatim.openstreetmap.org/search"
    params = {
        'q': cleaned_address,
        'format': 'json',
        'limit': 1,
    }
    headers = {
        'User-Agent': 'Django Volunteer App (for testing only)'
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
    except Exception as e:
        print(f"[Geocode ERROR] Address parsing failed: {cleaned_address} → {e}")
    return None, None

def send_activation_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    activation_url = request.build_absolute_uri(
        reverse('user:activate', kwargs={'uidb64': uid, 'token': token})
    )

    subject = "Activate Your Account"
    message = f"""\
Hi {user.email},

Thank you for registering on our platform.

To activate your account, please click the link below:

{activation_url}

If you did not sign up for this account, you can safely ignore this email.

Best regards,  
The Support Team
"""

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
