from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from wallet.models import Wallet
from orders.models import Order

# Create your views here.

@login_required
def dashboard(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    total_orders = Order.objects.filter(user=request.user).count()

    return render(request, 'accounts/dashboard.html', {
        'wallet': wallet,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
    })


def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')

        if not identifier or not password:
            messages.error(request, 'Please provide both identifier and password.')
            return render(request, 'accounts/login.html', {})

        # Allow login by either email or username. Our auth backend uses
        # email as the USERNAME_FIELD, so we resolve the user's email first.
        user_obj = None
        if '@' in identifier:
            try:
                user_obj = CustomUser.objects.get(email__iexact=identifier)
            except CustomUser.DoesNotExist:
                user_obj = None
        else:
            try:
                user_obj = CustomUser.objects.get(username__iexact=identifier)
            except CustomUser.DoesNotExist:
                user_obj = None

        if user_obj is None:
            messages.error(request, 'Invalid email/username or password.')
            return render(request, 'accounts/login.html', {})

        try:
            # Authenticate using the user's username (USERNAME_FIELD)
            user = authenticate(request, username=user_obj.username, password=password)
        except Exception:
            messages.error(request, 'Invalid email/username or password.')
            return render(request, 'accounts/login.html', {})

        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email/username or password.')
    
    return render(request, 'accounts/login.html', {})


def register_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not identifier or not password1 or not password2:
            messages.error(request, 'All fields are required.')
            return render(request, 'accounts/register.html', {})

        # Validate passwords match and length
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html', {})

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'accounts/register.html', {})

        # Determine whether identifier is email or username, then ensure
        # uniqueness for both email and username.
        username = None
        email = None
        if '@' in identifier:
            # Treat as email
            email = identifier.strip().lower()
            if CustomUser.objects.filter(email__iexact=email).exists():
                messages.error(request, 'An account with this email already exists.')
                return render(request, 'accounts/register.html', {})

            base_username = email.split('@')[0]
            username = base_username
            # Ensure username uniqueness by appending numbers if needed
            suffix = 0
            while CustomUser.objects.filter(username__iexact=username).exists():
                suffix += 1
                username = f"{base_username}{suffix}"
        else:
            # Treat as username; keep email empty if user didn't provide one
            username = identifier.strip()
            if CustomUser.objects.filter(username__iexact=username).exists():
                messages.error(request, 'An account with this username already exists.')
                return render(request, 'accounts/register.html', {})

            email = None

        try:
            user = CustomUser.objects.create_user(email=email, username=username, password=password1)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'accounts/register.html', {})
    
    return render(request, 'accounts/register.html', {})


def logout_view(request):
    logout(request)
    return redirect('login')