"""
EXPAY PAYMENT GATEWAY INTEGRATION GUIDE

This document provides step-by-step instructions for integrating ExPay
into your existing Razorpay-based checkout flows.

Generated for hazumake project
==============================================================================
"""

# ═══════════════════════════════════════════════════════════════════════════
# 1. WALLET TOP-UP INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

"""
FILE: wallet/views.py

Replace the Razorpay wallet_topup and razorpay_create_order views with
ExPay-based equivalents.

OLD FLOW (Razorpay):
  1. User enters amount
  2. Backend creates Razorpay order via client.order.create()
  3. Frontend redirects to Razorpay hosted checkout
  4. Razorpay calls POST back to wallet_topup view
  5. Signature verified with Razorpay client.utility.verify_payment_signature()
  6. Wallet credited if verified

NEW FLOW (ExPay):
  1. User enters amount
  2. Backend creates ExPay order via ExPayAPI.create_order()
  3. Backend redirects user to ExPay payment_url
  4. ExPay processes payment and calls webhook (/api/wallet/webhook/)
  5. Webhook verifies HMAC-SHA256 signature and credits wallet
  6. Optional: User polls status OR checks wallet directly

"""

# --- NEW WALLET TOP-UP VIEW (ExPay) ---

WALLET_TOPUP_NEW = '''
import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render

from services.payments.expay_api import get_client as get_expay_client, ExPayError
from .models import Transaction, Wallet


@login_required
def wallet_topup(request):
    """Display wallet page with transaction history."""
    wallet = request.user.wallet

    wallet_balance = wallet.balance
    transactions_list = wallet.transactions.all().order_by('-created_at')
    paginator = Paginator(transactions_list, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'wallet_balance': wallet_balance,
        'transactions': transactions,
    })


@login_required
def expay_create_order(request):
    """Create ExPay order for wallet top-up.
    
    Request:
        POST JSON: {"amount": "100"}
    
    Response:
        JSON: {
            "status": true,
            "payment_url": "https://exgateway2.in/paymentX/instant-pay/...",
            "message": "Order created. Redirecting to payment gateway."
        }
    """
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

    if amount_value > Decimal('100000'):
        return JsonResponse({'error': 'Maximum top-up amount is ₹100,000.'}, status=400)

    try:
        expay_api = get_expay_client()
        
        # Generate unique order ID
        import time
        order_id = f"topup_{request.user.id}_{int(time.time() * 1000)}"
        
        # Create ExPay order
        result = expay_api.create_order(
            customer_mobile=request.user.profile.phone or '9000000000',  # adjust based on your CustomUser model
            amount=str(amount_value),
            order_id=order_id,
            remark1=f"user_{request.user.id}",
            remark2="wallet_topup",
        )
        
        # Save order reference for later verification (optional, webhook handles it)
        # WalletTopup.objects.create(
        #     user=request.user,
        #     order_id=order_id,
        #     expay_order_id=result["orderId"],
        #     amount=amount_value,
        # )
        
        return JsonResponse({
            'status': True,
            'payment_url': result['payment_url'],
            'order_id': result['orderId'],
            'message': 'Order created. Redirecting to payment gateway.'
        })
    
    except ExPayError as exc:
        return JsonResponse({'error': str(exc), 'status': False}, status=400)
    except Exception as exc:
        return JsonResponse({'error': f'Unexpected error: {str(exc)}', 'status': False}, status=500)
'''

# ═══════════════════════════════════════════════════════════════════════════
# 2. PRODUCT ORDER PAYMENT (GAME TOP-UP) INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

"""
FILE: orders/views.py

The place_order view currently supports two payment methods:
  - WALLET: Deduct from user wallet (already works, no changes needed)
  - RAZORPAY: Create Razorpay order and verify in razorpay_order_success

To add ExPay, add a third payment method: EXPAY

OLD RAZORPAY FLOW:
  1. User selects game/product and clicks buy
  2. place_order() creates Razorpay order
  3. Razorpay order data returned to frontend
  4. Frontend opens Razorpay checkout modal
  5. User pays
  6. Razorpay calls POST to razorpay_order_success view
  7. Signature verified, Order created, Smile.one fulfillment triggered

NEW EXPAY FLOW:
  1. User selects game/product and clicks buy
  2. place_order() creates ExPay order
  3. ExPay order data returned to frontend (payment_url)
  4. Frontend redirects user to payment_url
  5. User pays on ExPay hosted page
  6. ExPay redirects user back to EXPAY_REDIRECT_URL (/payment/return/)
  7. User is redirected to /orders/ (or custom return page)
  8. Simultaneously, ExPay calls webhook (/api/wallet/webhook/)
  9. Webhook verifies signature, creates Order, triggers Smile.one

The key difference: With ExPay, you don't need a POST callback view.
The webhook handles everything server-to-server. The user redirect
is just for UX (confirming payment).

"""

# --- UPDATED place_order VIEW (add EXPAY case) ---

PLACE_ORDER_EXPAY_CASE = '''
    # ─── EXPAY PAYMENT ────────────────────────────────────────────
    if payment_method == 'EXPAY':
        from services.payments.expay_api import get_client as get_expay_client, ExPayError
        import time
        
        try:
            # Generate unique order ID
            order_id = f"order_{request.user.id}_{int(time.time() * 1000)}"
            
            # Create ExPay order
            expay_api = get_expay_client()
            result = expay_api.create_order(
                customer_mobile=request.user.profile.phone or '9000000000',
                amount=str(total_inr),
                order_id=order_id,
                remark1=f"user_{request.user.id}",
                remark2=f"product_{product.id}",
            )
            
            # Save pending order state in session for webhook correlation
            # (The webhook will look up orders by smile_order_id if available,
            #  but we can store this for debugging/fallback)
            request.session['pending_expay_order'] = {
                'product_id': str(product.id),
                'player_fields': player_fields,
                'quantity': quantity,
                'total_coins': total_coins,
                'total_inr': str(total_inr),
                'expay_order_id': result['orderId'],
                'local_order_id': order_id,
            }
            
            return JsonResponse({
                'payment_url': result['payment_url'],
                'expay_order_id': result['orderId'],
                'local_order_id': order_id,
            })
        
        except ExPayError as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        except Exception as exc:
            logger.exception("ExPay order creation failed: %s", exc)
            return JsonResponse({'error': 'Payment gateway error'}, status=500)
'''

# ═══════════════════════════════════════════════════════════════════════════
# 3. WEBHOOK HANDLING (Already implemented in payments/views.py)
# ═══════════════════════════════════════════════════════════════════════════

"""
The webhook handler at /api/wallet/webhook/ will:

1. Receive ExPay PAYMENT_SUCCESS event
2. Verify HMAC-SHA256 signature
3. Look up Order by smile_order_id (from orderId field)
4. Mark order as COMPLETED
5. Credit user wallet if needed (for wallet top-ups)
6. Log transaction

No changes needed from you — the webhook is automatic.

HOWEVER, you may want to customize the wallet crediting logic.
Currently, it credits based on order.quantity, but your app may
store coin amounts differently. Review and update:
  payments/views.py → _mark_order_completed()
"""

# ═══════════════════════════════════════════════════════════════════════════
# 4. FRONTEND INTEGRATION (JavaScript)
# ═══════════════════════════════════════════════════════════════════════════

"""
You need to update your frontend to:
1. Send EXPAY as payment_method to place_order
2. Redirect user to payment_url instead of opening a modal
3. Handle return (optional status check)

Example: products/templates/products/product_detail.html

OLD CODE (Razorpay):
  // Create Razorpay order first
  const response = await fetch('/orders/create/', {
    method: 'POST',
    body: JSON.stringify({...checkout data, payment_method: 'RAZORPAY'}),
  });
  const data = await response.json();
  
  // Open Razorpay modal
  const options = {
    key: data.key_id,
    order_id: data.razorpay_order_id,
    ...
  };
  razorpay.open(options);

NEW CODE (ExPay):
  const response = await fetch('/orders/create/', {
    method: 'POST',
    body: JSON.stringify({...checkout data, payment_method: 'EXPAY'}),
  });
  const data = await response.json();
  
  if (data.payment_url) {
    // Redirect to ExPay hosted payment page
    window.location.href = data.payment_url;
  }
"""

# ═══════════════════════════════════════════════════════════════════════════
# 5. DATABASE NOTES
# ═══════════════════════════════════════════════════════════════════════════

"""
Your Order model should store the ExPay order ID for tracking.
Currently, you use:
  - order.smile_order_id: Smile.one fulfillment order ID
  
You may want to add:
  - order.payment_gateway: 'RAZORPAY' | 'EXPAY' | 'WALLET'
  - order.payment_transaction_id: ExPay's orderId (for webhook lookup)

The webhook in payments/views.py looks up orders by:
  Order.objects.get(smile_order_id=order_id)

This assumes orderId from ExPay is stored in smile_order_id.
If not, adjust the webhook lookup or add a new field.

CURRENT FLOW:
  ExPay orderId → stored in ??? → webhook looks up Order
  
Recommended: Store ExPay orderId in a new field:
  payment_transaction_id = models.CharField(...)
  
Then update webhook:
  order = Order.objects.get(payment_transaction_id=order_id)
"""

# ═══════════════════════════════════════════════════════════════════════════
# 6. TESTING THE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

"""
Once deployed:

1. In ExPay Dashboard:
   - Set Webhook URL: https://hazumakestore.com/api/wallet/webhook/
   - Enable webhook deliveries
   
2. Test webhook (ExPay dashboard → "Send Test Webhook"):
   - Dashboard will send a test PAYMENT_SUCCESS event
   - Check Django logs: you should see "ExPay webhook event=... status=..."
   - Verify response is HTTP 200
   
3. Test actual flow:
   - User tries to topup wallet or buy product
   - Payment page opens
   - Complete payment with test card (ExPay provides test cards)
   - Check Order/Wallet updated in admin
   - Check Django logs for webhook signature verification
   
4. Troubleshooting:
   - Enable DEBUG=True in .env for verbose logging
   - Check /hazumake-control/ (Django admin) → Orders → verify status
   - Check /hazumake-control/ → Wallet → verify balance
   - In logs, search for "ExPay webhook" to see webhook processing
"""

# ═══════════════════════════════════════════════════════════════════════════
# 7. URLS SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

"""
NEW ENDPOINTS (ExPay integration):

1. Webhook (server-to-server):
   POST /api/wallet/webhook/
   → Receives ExPay payment notifications
   → Verifies HMAC-SHA256 signature
   → Updates Order/Wallet
   → Always returns HTTP 200

2. Frontend redirects to ExPay:
   (No Django endpoint needed, direct redirect to payment_url)
   https://exgateway2.in/paymentX/instant-pay/?token=...

3. Return URL (optional UX):
   POST /payment/return/  (configured in .env as EXPAY_REDIRECT_URL)
   → Can show "Payment successful" or redirect to /orders/
   → Webhook already processed payment server-side

"""

# ═══════════════════════════════════════════════════════════════════════════
# 8. DEPLOYMENT CHECKLIST
# ═══════════════════════════════════════════════════════════════════════════

CHECKLIST = """
☐ 1. Created services/payments/expay_api.py
☐ 2. Created payments app with views.py, urls.py
☐ 3. Added 'payments' to INSTALLED_APPS
☐ 4. Added ExPay settings to settings.py
☐ 5. Updated root urls.py to include payments URLs
☐ 6. Updated .env with EXPAY_USER_TOKEN, EXPAY_WEBHOOK_SECRET
☐ 7. Updated wallet/views.py to support ExPay
☐ 8. Updated orders/views.py to support ExPay in place_order()
☐ 9. Updated frontend JS to redirect to payment_url for ExPay
☐ 10. Updated Order model if needed (payment_transaction_id field)
☐ 11. Tested webhook locally with ngrok or similar
☐ 12. Deployed to production
☐ 13. Registered webhook URL in ExPay dashboard
☐ 14. Tested actual payment flow end-to-end
☐ 15. Monitored logs for any issues
☐ 16. Removed old KhilaadiXPro/Razorpay SDKs from codebase
"""

print(CHECKLIST)
