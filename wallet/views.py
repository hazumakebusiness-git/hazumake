# Create your views here.
import json
import logging
import time
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render

from services.payments.expay_api import get_client as get_expay_client, ExPayError
from .models import Transaction, WalletTopup

logger = logging.getLogger(__name__)

@login_required
def wallet_topup(request):
    wallet = request.user.wallet
    wallet_inr_estimate = wallet.balance
    transactions_list = wallet.transactions.all().order_by('-created_at')
    paginator = Paginator(transactions_list, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'wallet_inr_estimate': wallet_inr_estimate,
        'transactions': transactions,
    })

@login_required
def expay_create_order(request):
    """Create an ExPay wallet top-up order."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    amount_str = payload.get('amount')
    if amount_str is None:
        return JsonResponse({'error': 'Amount is required.'}, status=400)

    try:
        amount_value = Decimal(str(amount_str))
    except (InvalidOperation, ValueError):
        return JsonResponse({'error': 'Invalid amount value.'}, status=400)

    if amount_value < Decimal('10'):
        return JsonResponse({'error': 'Minimum top-up amount is ₹10.'}, status=400)

    try:
        # Create unique order ID
        order_id = f"walletup_{request.user.id}_{int(time.time() * 1000)}"
        
        # Call ExPay API to create order
        api = get_expay_client()
        result = api.create_order(
            customer_mobile=request.user.phone or '9000000000',
            amount=str(amount_value),
            order_id=order_id,
            remark1=f'wallet_topup_user_{request.user.id}',
            remark2='hazumake_wallet',
        )
        
        # Save WalletTopup record for tracking
        WalletTopup.objects.create(

            user=request.user,
            payment_transaction_id=result['orderId'],
            amount=amount_value,
            status='PENDING',
            )
        
        logger.info('Created ExPay order %s for user %s, amount ₹%s', result['orderId'], request.user.email, amount_value)
        
        return JsonResponse({
            'payment_url': result['payment_url'],
            'expay_order_id': result['orderId'],
            'order_id': order_id,
        })
    except ExPayError as exc:
        logger.error('ExPay error creating order: %s', exc)
        return JsonResponse({'error': f'Payment gateway error: {str(exc)}'}, status=400)
    except Exception as exc:
        logger.exception('Error creating ExPay order: %s', exc)
        return JsonResponse({'error': 'An error occurred. Please try again.'}, status=500)