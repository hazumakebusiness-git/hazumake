import random

from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def build_username_from_identifier(identifier):
    raw = identifier.strip()
    if '@' in raw:
        base = raw.split('@')[0]
        base = ''.join(ch for ch in base if ch.isalnum() or ch == '_')[:120]
        if not base:
            base = 'user'
        return base
    return raw.lstrip('+').replace('+', '').replace('-', '').replace(' ', '')[:140] or 'user'


def send_email_otp(email, code):
    subject = 'Your Hazumake OTP Code'
    message = f'Your Hazumake OTP code is {code}. It expires in 10 minutes.'
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email], fail_silently=False)


def send_sms_otp(phone, code):
    try:
        from twilio.rest import Client
    except ImportError:
        raise RuntimeError('Twilio SDK is not installed')

    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_FROM_NUMBER

    if not account_sid or not auth_token or not from_number:
        raise RuntimeError('Twilio is not configured')

    client = Client(account_sid, auth_token)
    client.messages.create(
        body=f'Your Hazumake OTP code is {code}. It expires in 10 minutes.',
        from_=from_number,
        to=phone,
    )
