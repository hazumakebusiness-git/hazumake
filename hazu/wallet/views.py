# Create your views here.
import json
from decimal import Decimal, InvalidOperation

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import Transaction

@login_required
def wallet_topup(request):
    wallet = request.user.wallet

    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
            messages.error(request, 'Payment verification failed.')
            return redirect('wallet')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })

            razorpay_order = client.order.fetch(razorpay_order_id)
            amount_paise = razorpay_order.get('amount')
            if amount_paise is None:
                raise ValueError('Unable to fetch Razorpay order amount.')

            amount_inr = Decimal(amount_paise) / Decimal('100')
            wallet.balance = wallet.balance + amount_inr
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                type='CREDIT',
                amount=amount_inr,
                balance_after=wallet.balance,
                note='Wallet top-up via Razorpay',
            )

            messages.success(request, f'₹{amount_inr:.2f} added to your wallet!')
            return redirect('wallet')

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, 'Payment verification failed.')
            return redirect('wallet')
        except Exception as exc:
            messages.error(request, f'Payment verification failed.')
            return redirect('wallet')

    wallet_inr_estimate = wallet.balance
    razorpay_key_id = settings.RAZORPAY_KEY_ID
    print("DEBUG KEY:", razorpay_key_id)  # add this line
    transactions_list = wallet.transactions.all().order_by('-created_at')
    paginator = Paginator(transactions_list, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'wallet_inr_estimate': wallet_inr_estimate,
        'razorpay_key_id': razorpay_key_id,
        'transactions': transactions,
    })

@csrf_exempt
@login_required
def razorpay_create_order(request):
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
        amount_paise = int(amount_value * Decimal('100'))
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = razorpay_client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1,
        })
        return JsonResponse({'order_id': razorpay_order['id'], 'amount': razorpay_order['amount']})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)