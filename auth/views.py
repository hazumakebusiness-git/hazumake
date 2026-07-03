import json
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
User = get_user_model()

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_ADMIN_CREDENTIALS)
    firebase_admin.initialize_app(cred)


def signin_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/accounts/login/')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/accounts/register/')


@csrf_protect
@require_POST
def firebase_session(request):
    try:
        body = json.loads(request.body)
        id_token = body.get('id_token')
        if not id_token:
            return JsonResponse({'error': 'No token provided'}, status=400)

        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')

        # First try to find existing user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user with a real (random, hashed) password so
            # they can also log in later via email/password if they set one
            random_password = get_random_string(32)
            user = User.objects.create_user(
                username=uid,
                email=email,
                password=random_password,
                first_name=decoded_token.get('name', '').split(' ')[0],
                last_name=' '.join(decoded_token.get('name', '').split(' ')[1:]),
                is_active=True,
                is_email_verified=decoded_token.get('email_verified', False),
            )

        # Ensure wallet exists
        try:
            from wallet.models import Wallet
            Wallet.objects.get_or_create(user=user)
        except Exception:
            pass

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return JsonResponse({'status': 'ok', 'email': email})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except firebase_auth.InvalidIdTokenError:
        return JsonResponse({'error': 'Invalid token'}, status=401)
    except firebase_auth.ExpiredIdTokenError:
        return JsonResponse({'error': 'Token expired'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def signout_view(request):
    logout(request)
    return redirect('/auth/signin/')
