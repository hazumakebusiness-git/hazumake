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


def register_view(request):
    """Redirect to Firebase sign-up."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/auth/signup/')


def register_view_legacy(request):
    """Register with email and password only. Requires OTP verification before dashboard access."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == "POST":
        email = request.POST.get('identifier', '').lower().strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Validation
        if not email or '@' not in email:
            messages.error(request, 'Please enter a valid email address')
            return redirect('register')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('register')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please login.')
            return redirect('login')
        
        # Create inactive user
        user = CustomUser.objects.create_user(
            email=email,
            password=password1,
            is_active=True,
            is_email_verified=False
        )
        
        # Generate and send OTP
        otp_code = generate_otp()
        OTPCode.objects.create(identifier=email, code=otp_code)
        send_email_otp(email, otp_code)
        
        # Store email in session for verification
        request.session['pending_email'] = email
        
        messages.success(request, f'Verification code sent to {email}')
        return redirect('verify_email')
    
    return render(request, 'accounts/register.html')


def verify_email_view(request):
    """Verify email with OTP code."""
    if request.user.is_authenticated and request.user.is_email_verified:
        return redirect('dashboard')
    
    pending_email = request.session.get('pending_email')
    
    if not pending_email:
        messages.error(request, 'No pending email verification. Please register first.')
        return redirect('register')
    
    if request.method == "POST":
        otp_code = request.POST.get('otp', '').strip()
        
        if not otp_code or len(otp_code) != 6:
            messages.error(request, 'Please enter a valid 6-digit code')
            return render(request, 'accounts/verify_email.html', {'email': pending_email})
        
        # Verify OTP
        try:
            otp = OTPCode.objects.get(identifier=pending_email, code=otp_code)
            
            if not otp.is_valid():
                messages.error(request, 'Code expired or already used. Request a new one.')
                return render(request, 'accounts/verify_email.html', {'email': pending_email})
            
            # Mark as used and verify email
            otp.is_used = True
            otp.save()
            
            user = CustomUser.objects.get(email=pending_email)
            user.is_email_verified = True
            user.save()
            
            # Clean up session and auto-login
            del request.session['pending_email']
            login(request, user)
            
            # Create wallet
            Wallet.objects.get_or_create(user=user)
            
            messages.success(request, 'Email verified successfully! Welcome to Hazumake.')
            return redirect('dashboard')
        
        except OTPCode.DoesNotExist:
            messages.error(request, 'Invalid verification code')
            return render(request, 'accounts/verify_email.html', {'email': pending_email})
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found. Please register again.')
            del request.session['pending_email']
            return redirect('register')
    
    return render(request, 'accounts/verify_email.html', {'email': pending_email})


def resend_otp_view(request):
    """Resend OTP to email."""
    pending_email = request.session.get('pending_email')
    
    if not pending_email:
        messages.error(request, 'No pending email verification')
        return redirect('register')
    
    # Delete old OTP codes
    OTPCode.objects.filter(identifier=pending_email).delete()
    
    # Generate and send new OTP
    otp_code = generate_otp()
    OTPCode.objects.create(identifier=pending_email, code=otp_code)
    send_email_otp(pending_email, otp_code)
    
    messages.success(request, f'New verification code sent to {pending_email}')
    return redirect('verify_email')


def login_view(request):
    """Redirect to Firebase sign-in."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/auth/signin/')


def login_view_legacy(request):
    """Login with email only (email-based authentication)."""
    if request.user.is_authenticated and request.user.is_email_verified:
        return redirect('dashboard')
    
    if request.method == "POST":
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')
        
        if not identifier or not password:
            messages.error(request, 'Email or username and password are required')
            return redirect('login')
        
        try:
            user = None
            if '@' in identifier:
                user = CustomUser.objects.filter(email__iexact=identifier).first()
            if not user:
                user = CustomUser.objects.filter(username__iexact=identifier).first()
            
            if not user:
                raise CustomUser.DoesNotExist
            
            authenticated_user = authenticate(request, username=user.email, password=password)
            
            if authenticated_user:
                if not authenticated_user.is_email_verified and not (authenticated_user.is_superuser or authenticated_user.is_staff):
                    # Generate OTP and send for verification for normal users only
                    otp_code = generate_otp()
                    OTPCode.objects.filter(identifier=user.email).delete()
                    OTPCode.objects.create(identifier=user.email, code=otp_code)
                    send_email_otp(user.email, otp_code)
                    
                    request.session['pending_email'] = user.email
                    messages.info(request, 'Please verify your email before accessing dashboard')
                    return redirect('verify_email')
                
                # Email is verified or user has elevated access, proceed with login
                login(request, authenticated_user)
                messages.success(request, f'Welcome back!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email/username or password')
                return redirect('login')
        
        except CustomUser.DoesNotExist:
            messages.error(request, 'Account not found. Please register first.')
            return redirect('register')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Logout user."""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('home')


@login_required(login_url='/auth/signin/')
def dashboard(request):
    """Dashboard requires authentication. Works with both CustomUser and Firebase User."""
    # Get or create wallet for the user
    try:
        from wallet.models import Wallet
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
    except:
        wallet = None
    
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    total_orders = Order.objects.filter(user=request.user).count()
    
    context = {
        'user': request.user,
        'wallet': wallet,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='/auth/signin/')
def change_password_view(request):
    """Client-side password change UI."""
    from accounts.forms import ChangePasswordForm
    
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data.get('current_password')
            new_password = form.cleaned_data.get('new_password')
            
            # Verify current password
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect')
                return render(request, 'accounts/change_password.html', {'form': form})
            
            # Update password
            request.user.set_password(new_password)
            request.user.save()
            
            # Re-login user to keep session active
            login(request, request.user)
            
            messages.success(request, 'Password changed successfully!')
            return redirect('password_change_done')
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ChangePasswordForm()
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/change_password.html', context)


@login_required(login_url='/auth/signin/')
def password_change_done(request):
    """Simple success page after password change."""
    return render(request, 'accounts/password_change_done.html')


# Custom Password Reset Views
class CustomPasswordResetView(PasswordResetView):
    """Custom password reset form view with our template."""
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reset Your Password'
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view with our template."""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Set New Password'
        return context


def password_reset_done_view(request):
    """Confirmation page after reset email is sent."""
    return render(request, 'accounts/password_reset_done.html', {
        'page_title': 'Password Reset Email Sent'
    })


def password_reset_complete_view(request):
    """Success page after password has been reset."""
    return render(request, 'accounts/password_reset_complete.html', {
        'page_title': 'Password Reset Successful'
    })