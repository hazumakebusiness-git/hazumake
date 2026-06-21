from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib import messages
from accounts.models import CustomUser, OTPCode
from wallet.models import Wallet
from orders.models import Order
from accounts.otp_utils import generate_otp, send_email_otp
from django.utils import timezone
from django.urls import reverse_lazy
import logging

logger = logging.getLogger(__name__)


# ─── REGISTER ────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/auth/signup/')


def register_view_legacy(request):
    """Step 1 of registration: collect email, send OTP."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()

        if not email or '@' not in email:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('register')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please login.')
            return redirect('login')

        # Send OTP
        otp_code = generate_otp()
        OTPCode.objects.filter(identifier=email, is_used=False).delete()
        OTPCode.objects.create(
            identifier=email,
            code=otp_code,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        send_email_otp(email, otp_code)

        request.session['pending_register_email'] = email
        messages.success(request, f'Verification code sent to {email}.')
        return redirect('verify_email')

    return render(request, 'accounts/register.html')


def verify_email_view(request):
    """Step 2 of registration: verify OTP."""
    if request.user.is_authenticated and request.user.is_email_verified:
        return redirect('dashboard')

    pending_email = request.session.get('pending_register_email')
    if not pending_email:
        messages.error(request, 'No pending registration. Please start again.')
        return redirect('register')

    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()

        try:
            otp = OTPCode.objects.filter(
                identifier=pending_email,
                code=otp_entered,
                is_used=False,
            ).latest('created_at')

            if not otp.is_valid():
                messages.error(request, 'Code expired. Please request a new one.')
                return render(request, 'accounts/verify_email.html', {'email': pending_email})

            otp.is_used = True
            otp.save()

            # Mark session as OTP verified, move to set password step
            request.session['otp_verified_email'] = pending_email
            del request.session['pending_register_email']
            return redirect('set_password')

        except OTPCode.DoesNotExist:
            messages.error(request, 'Invalid code. Please try again.')
            return render(request, 'accounts/verify_email.html', {'email': pending_email})

    return render(request, 'accounts/verify_email.html', {'email': pending_email})


def set_password_view(request):
    """Step 3 of registration: set password and create account."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    email = request.session.get('otp_verified_email')
    if not email:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('register')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'accounts/set_password.html', {'email': email})

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/set_password.html', {'email': email})

        # Create user
        user = CustomUser.objects.create_user(
            email=email,
            password=password1,
            is_active=True,
            is_email_verified=True,
        )
        Wallet.objects.get_or_create(user=user)

        del request.session['otp_verified_email']

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Account created! Welcome to Hazumake.')
        return redirect('dashboard')

    return render(request, 'accounts/set_password.html', {'email': email})


def resend_otp_view(request):
    """Resend OTP for registration."""
    pending_email = request.session.get('pending_register_email')
    if not pending_email:
        messages.error(request, 'No pending registration.')
        return redirect('register')

    OTPCode.objects.filter(identifier=pending_email, is_used=False).delete()
    otp_code = generate_otp()
    OTPCode.objects.create(
        identifier=pending_email,
        code=otp_code,
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
    )
    send_email_otp(pending_email, otp_code)
    messages.success(request, f'New code sent to {pending_email}.')
    return redirect('verify_email')


# ─── LOGIN ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/auth/signin/')


def login_view_legacy(request):
    """Login: email + password only. No OTP required."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect('login')

        authenticated_user = authenticate(request, username=email, password=password)

        if authenticated_user:
            login(request, authenticated_user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Welcome back!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@login_required(login_url='/auth/signin/')
def dashboard(request):
    try:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
    except:
        wallet = None

    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    total_orders = Order.objects.filter(user=request.user).count()

    return render(request, 'dashboard.html', {
        'user': request.user,
        'wallet': wallet,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
    })


# ─── PASSWORD CHANGE ─────────────────────────────────────────────────────────

@login_required(login_url='/auth/signin/')
def change_password_view(request):
    from accounts.forms import ChangePasswordForm

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data.get('current_password')
            new_password = form.cleaned_data.get('new_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return render(request, 'accounts/change_password.html', {'form': form})

            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Password changed successfully!')
            return redirect('password_change_done')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ChangePasswordForm()

    return render(request, 'accounts/change_password.html', {'form': form, 'user': request.user})


@login_required(login_url='/auth/signin/')
def password_change_done(request):
    return render(request, 'accounts/password_change_done.html')


# ─── PASSWORD RESET ──────────────────────────────────────────────────────────

class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reset Your Password'
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Set New Password'
        return context


def password_reset_done_view(request):
    return render(request, 'accounts/password_reset_done.html', {'page_title': 'Password Reset Email Sent'})


def password_reset_complete_view(request):
    return render(request, 'accounts/password_reset_complete.html', {'page_title': 'Password Reset Successful'})