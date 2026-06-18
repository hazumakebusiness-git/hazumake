"""
EXPAY_CODE_SNIPPETS.md

Copy-paste ready code for wallet/views.py and orders/views.py updates
=====================================================================
"""

# ═══════════════════════════════════════════════════════════════════════════
# WALLET/VIEWS.PY - NEW EXPAY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

"""
1. Replace the razorpay_create_order function with expay_create_order

Step 1: Update imports at top of wallet/views.py:
"""

WALLET_IMPORTS = """
import json
import time
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from services.payments.expay_api import get_client as get_expay_client, ExPayError
from .models import Transaction

import logging
logger = logging.getLogger(__name__)
"""

"""
2. REPLACE THIS FUNCTION:
@csrf_exempt
@login_required
def razorpay_create_order(request):
    ...

WITH THIS:
"""

NEW_EXPAY_ENDPOINT = """
@login_required
def expay_create_order(request):
    '''
    Create ExPay order for wallet top-up.
    
    POST /wallet/create-order/
    Body: {"amount": "100"}
    
    Response: {
        "status": true,
        "payment_url": "https://exgateway2.in/paymentX/instant-pay/...",
        "expay_order_id": "1234561705047510"
    }
    '''
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    try:
        payload = json.loads(
            request.body.decode('utf-8') 
            if isinstance(request.body, bytes) 
            else request.body
        )
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
        order_id = f"topup_{request.user.id}_{int(time.time() * 1000)}"
        
        # Create ExPay order
        result = expay_api.create_order(
            customer_mobile=request.user.profile.phone or '9000000000',
            amount=str(amount_value),
            order_id=order_id,
            remark1=f"user_{request.user.id}",
            remark2="wallet_topup",
        )
        
        logger.info(
            "ExPay order created: order_id=%s amount=%s user=%s",
            order_id, amount_value, request.user.email
        )
        
        return JsonResponse({
            'status': True,
            'payment_url': result['payment_url'],
            'expay_order_id': result['orderId'],
            'message': 'Order created. Redirecting to payment gateway.'
        })
    
    except ExPayError as exc:
        logger.error("ExPay error: %s", exc)
        return JsonResponse(
            {'error': str(exc), 'status': False}, 
            status=400
        )
    except Exception as exc:
        logger.exception("Unexpected error in expay_create_order: %s", exc)
        return JsonResponse(
            {'error': f'Unexpected error: {str(exc)}', 'status': False}, 
            status=500
        )
"""

"""
3. UPDATE wallet/urls.py:

OLD:
    path('create-order/', views.razorpay_create_order, name='razorpay_create_order'),

NEW:
    path('create-order/', views.expay_create_order, name='expay_create_order'),
"""

# ═══════════════════════════════════════════════════════════════════════════
# ORDERS/VIEWS.PY - ADD EXPAY PAYMENT METHOD
# ═══════════════════════════════════════════════════════════════════════════

"""
In orders/views.py, find the place_order function.

Locate this section (around line 165-200):
    if payment_method == 'RAZORPAY':
        try:
            amount_paise = int(total_inr * Decimal('100'))
        ...
        return JsonResponse({...})
    
    return HttpResponseBadRequest('Invalid payment method.')

REPLACE THE ENTIRE "return HttpResponseBadRequest" line and add EXPAY case:
"""

ADD_EXPAY_TO_PLACE_ORDER = """
    # ─── EXPAY PAYMENT ────────────────────────────────────────────
    if payment_method == 'EXPAY':
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
            
            # Save pending order state in session
            request.session['pending_expay_order'] = {
                'product_id': str(product.id),
                'player_fields': player_fields,
                'quantity': quantity,
                'total_coins': total_coins,
                'total_inr': str(total_inr),
                'expay_order_id': result['orderId'],
                'local_order_id': order_id,
            }
            
            logger.info(
                "ExPay order created for product purchase: product=%s amount=%s user=%s",
                product.id, total_inr, request.user.email
            )
            
            return JsonResponse({
                'payment_url': result['payment_url'],
                'expay_order_id': result['orderId'],
                'local_order_id': order_id,
            })
        
        except ExPayError as exc:
            logger.error("ExPay error in place_order: %s", exc)
            return JsonResponse({'error': str(exc)}, status=400)
        except Exception as exc:
            logger.exception("Unexpected error in ExPay place_order: %s", exc)
            return JsonResponse({'error': 'Payment gateway error'}, status=500)

    return HttpResponseBadRequest('Invalid payment method.')
"""

"""
UPDATE orders/views.py imports:
Add after existing imports:
"""

ADD_TO_ORDERS_IMPORTS = """
import time
from services.payments.expay_api import get_client as get_expay_client, ExPayError
"""

# ═══════════════════════════════════════════════════════════════════════════
# FRONTEND - PAYMENT METHOD SELECTION
# ═══════════════════════════════════════════════════════════════════════════

"""
Update your checkout form/template to include EXPAY option.

In products/templates/products/product_detail.html or wallet/wallet.html:

BEFORE:
<input type="radio" name="payment_method" value="RAZORPAY" checked>
Razorpay (Card/UPI/Wallet)

AFTER:
<input type="radio" name="payment_method" value="EXPAY">
ExPay (Fast & Secure)

<input type="radio" name="payment_method" value="RAZORPAY">
Razorpay (Card/UPI/Wallet)

<input type="radio" name="payment_method" value="WALLET">
Wallet Balance
"""

# ═══════════════════════════════════════════════════════════════════════════
# FRONTEND - JAVASCRIPT CHANGES
# ═══════════════════════════════════════════════════════════════════════════

"""
OLD CHECKOUT FLOW (Razorpay):
"""

OLD_CHECKOUT_JS = """
// Create order first
const response = await fetch('/orders/create/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        product_id: productId,
        payment_method: 'RAZORPAY',
        ...playerFields
    })
});

const data = await response.json();

// Open Razorpay modal
const options = {
    key: data.key_id,
    order_id: data.razorpay_order_id,
    amount: data.amount_paise,
    currency: 'INR',
    handler: function(response) {
        // Send verification form
        document.getElementById('razorpay_payment_id').value = response.razorpay_payment_id;
        document.getElementById('razorpay_order_id').value = response.razorpay_order_id;
        document.getElementById('razorpay_signature').value = response.razorpay_signature;
        document.getElementById('paymentForm').submit();
    },
};
const razorpay = new Razorpay(options);
razorpay.open();
"""

"""
NEW CHECKOUT FLOW (ExPay + Razorpay):
"""

NEW_CHECKOUT_JS = """
const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;

const response = await fetch('/orders/create/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        product_id: productId,
        payment_method: paymentMethod,
        ...playerFields
    })
});

const data = await response.json();

if (paymentMethod === 'EXPAY') {
    // Redirect to ExPay hosted payment page
    if (data.payment_url) {
        window.location.href = data.payment_url;
    } else {
        alert('Payment gateway error: ' + (data.error || 'Unknown error'));
    }
}
else if (paymentMethod === 'RAZORPAY') {
    // Open Razorpay modal (old code)
    const options = {
        key: data.key_id,
        order_id: data.razorpay_order_id,
        amount: data.amount_paise,
        ...
    };
    const razorpay = new Razorpay(options);
    razorpay.open();
}
else if (paymentMethod === 'WALLET') {
    // Submit form directly for wallet payment
    document.getElementById('paymentForm').submit();
}
"""

# ═══════════════════════════════════════════════════════════════════════════
# ORDER MODEL (OPTIONAL - for tracking)
# ═══════════════════════════════════════════════════════════════════════════

"""
In orders/models.py, add this field to the Order model:
"""

ADD_TO_ORDER_MODEL = """
class Order(models.Model):
    # ... existing fields ...
    
    # NEW: Payment gateway transaction tracking
    payment_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ExPay orderId or payment gateway transaction ID"
    )
    
    class Meta:
        # ... existing meta ...
        indexes = [
            models.Index(fields=['payment_transaction_id']),
            models.Index(fields=['smile_order_id']),
        ]
"""

"""
Then run:
    python manage.py makemigrations orders
    python manage.py migrate
"""

# ═══════════════════════════════════════════════════════════════════════════
# WEBHOOK VERIFICATION (Already Implemented!)
# ═══════════════════════════════════════════════════════════════════════════

"""
No changes needed! The webhook at payments/views.py is complete.

But for reference, here's how it verifies the signature:

POST /api/wallet/webhook/ receives:
    Headers:
        X-ExPay-Signature: t=<timestamp>, v1=<hmac_hex>
        X-ExPay-Timestamp: <timestamp>
    
    Body (JSON):
        {"event": "PAYMENT_SUCCESS", "orderId": "...", ...}

Verification:
    signed_payload = f"{timestamp}.{raw_body}"
    expected = hmac_sha256(EXPAY_WEBHOOK_SECRET, signed_payload)
    compare_constant_time(expected, v1_from_header)
"""

print("✅ Code snippets ready to copy-paste!")
