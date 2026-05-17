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
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'accounts/login.html', {})


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        else:
            try:
                user = CustomUser.objects.create_user(email=email, username=username, password=password1)
                login(request, user)
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    return render(request, 'accounts/register.html', {})


def logout_view(request):
    logout(request)
    return redirect('login')