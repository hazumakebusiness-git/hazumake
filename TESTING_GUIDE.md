"""
TESTING_GUIDE.md

Complete testing guide for ExPay payment gateway integration
============================================================
"""

# ═══════════════════════════════════════════════════════════════════════════
# PART 1: LOCAL TESTING (WITHOUT REAL PAYMENT)
# ═══════════════════════════════════════════════════════════════════════════

LOCAL_TESTING = """
═══════════════════════════════════════════════════════════════════════════
PART 1: LOCAL TESTING (WITHOUT REAL PAYMENT)
═══════════════════════════════════════════════════════════════════════════

Purpose: Verify code works and API integration is correct
Time: 30 minutes
Prerequisites: Django running locally (python manage.py runserver)

STEP 1: Test Django Setup
──────────────────────────
1. Start Django: python manage.py runserver
2. Verify no import errors:
   - Check console for errors
   - No message "ModuleNotFoundError: No module named 'payments'"
   
3. Test API import:
   python manage.py shell
   >>> from services.payments.expay_api import get_client
   >>> client = get_client()
   >>> print(client.user_token)  # Should print token from .env
   
4. Exit shell: exit()

STEP 2: Test Payment Method Selection
──────────────────────────────────────
1. Login to http://localhost:8000/accounts/login/
2. Navigate to /shop/ (shop page)
3. Click on a product
4. Scroll to payment method selection
5. Verify EXPAY option appears (you'll add this in view updates)

STEP 3: Test Form Submission (Flow Test)
──────────────────────────────────────────
1. Select a product and player details
2. Select EXPAY as payment method
3. Click "Buy Now" or similar
4. Check Django console for errors
5. Verify request reaches backend (no 404)
6. Check if API call was attempted (look for error or success message)

STEP 4: Test Wallet Top-up
────────────────────────────
1. Navigate to /wallet/
2. Enter an amount (e.g., 100)
3. Select EXPAY as payment method
4. Click "Top-up" or similar
5. Check for errors in Django console
6. Verify ExPay order creation attempt

EXPECTED RESULTS:
✅ No import errors
✅ Payment method selection works
✅ Form submission reaches backend
✅ No 500 errors in console
❌ May see "connection refused" for ExPay API (that's OK for now)
"""

print(LOCAL_TESTING)

# ═══════════════════════════════════════════════════════════════════════════
# PART 2: WEBHOOK TESTING (LOCAL WITH NGROK)
# ═══════════════════════════════════════════════════════════════════════════

WEBHOOK_TESTING = """
═══════════════════════════════════════════════════════════════════════════
PART 2: WEBHOOK TESTING (LOCAL WITH NGROK)
═══════════════════════════════════════════════════════════════════════════

Purpose: Verify webhook signature verification works correctly
Time: 20 minutes
Prerequisites: 
  - Django running on localhost:8000
  - ngrok installed (pip install ngrok or download)

STEP 1: Install and Start ngrok
─────────────────────────────────
# Download from https://ngrok.com/download (if not installed)
# Or install via pip: pip install ngrok

# Start ngrok:
ngrok http 8000

# You'll see output like:
# ngrok is running...
# https://12345678.ngrok.io forwarded to localhost:8000

COPY THE HTTPS URL (e.g., https://12345678.ngrok.io)

STEP 2: Configure ExPay Webhook
────────────────────────────────
1. Go to ExPay Dashboard: https://exgateway2.in/dashboard/
2. Navigate to Webhook Settings
3. Set Webhook URL: https://12345678.ngrok.io/api/wallet/webhook/
4. Set Webhook Secret: (should match EXPAY_WEBHOOK_SECRET in .env)
5. Save settings

STEP 3: Send Test Webhook
──────────────────────────
1. In ExPay Dashboard, click "Send Test Webhook"
2. Select: PAYMENT_SUCCESS event
3. Click "Send"

WHAT TO EXPECT:
────────────────
In Django console (python manage.py runserver):
  "ExPay webhook event=PAYMENT_SUCCESS order=... status=SUCCESS"

If signature verification passes:
  ✅ Message appears in logs
  ✅ Order should be marked COMPLETED (if it exists)
  
If signature verification fails:
  ❌ Message "ExPay webhook: signature mismatch" appears
  ❌ Check EXPAY_WEBHOOK_SECRET matches dashboard value

STEP 4: Verify Response
────────────────────────
ExPay expects HTTP 200 response.
Check ExPay Dashboard → Webhook History:
  ✅ Webhook status shows "Success" or "200"
  ✅ Response time should be < 1 second

If failing:
  ❌ Check Django is running and accessible
  ❌ Check ngrok forwarding is working
  ❌ Check firewall allows connections

STEP 5: Debug Failed Webhook
──────────────────────────────
Check Django logs for:
  - "ExPay webhook event=" (log entry exists?)
  - Signature verification messages
  - "Order not found" (order doesn't exist for this orderId)
  - Exception messages

If "Order not found":
  This is expected for test webhook (no real order created)
  The webhook handler returns HTTP 200 anyway

STEP 6: Create a Real Order First, Then Test Webhook
──────────────────────────────────────────────────────
1. Go to /shop/ → select product
2. Enter player details
3. DON'T complete payment (just test form)
4. In Django shell, create test Order:

python manage.py shell
>>> from orders.models import Order
>>> from products.models import Product, Game
>>> from accounts.models import CustomUser
>>> from decimal import Decimal
>>> user = CustomUser.objects.first()  # Your test user
>>> product = Product.objects.first()  # Any product
>>> game = Game.objects.first()  # Any game
>>> order = Order.objects.create(
...     user=user,
...     product=product,
...     game=game,
...     smile_order_id="test_webhook_order_123",
...     status="PENDING",
...     payment_method="EXPAY",
...     payment_status="UNPAID",
...     total_coins=100,
...     total_inr=Decimal('100.00'),
...     player_uid="test_uid",
... )
>>> print(f"Created order {order.id} with smile_order_id {order.smile_order_id}")
>>> exit()

Now test webhook with this real order's smile_order_id.

EXPECTED RESULT:
  ✅ Order status changes from PENDING to COMPLETED
  ✅ Wallet is credited (if applicable)
  ✅ No errors in logs
"""

print(WEBHOOK_TESTING)

# ═══════════════════════════════════════════════════════════════════════════
# PART 3: API TESTING
# ═══════════════════════════════════════════════════════════════════════════

API_TESTING = """
═══════════════════════════════════════════════════════════════════════════
PART 3: API TESTING (DIRECT FUNCTION CALLS)
═══════════════════════════════════════════════════════════════════════════

Purpose: Test ExPay API client directly
Time: 15 minutes

STEP 1: Test create_order()
──────────────────────────
python manage.py shell

>>> from services.payments.expay_api import get_client, ExPayError
>>> import time
>>> 
>>> client = get_client()
>>> 
>>> # Create test order
>>> result = client.create_order(
...     customer_mobile='9000000000',
...     amount='10',
...     order_id=f'test_{int(time.time() * 1000)}',
...     remark1='test_user_1',
...     remark2='test_topup'
... )
>>> 
>>> print(result)
{'orderId': '1234561705047510', 'payment_url': 'https://...'}

EXPECTED OUTPUT:
✅ Dictionary with 'orderId' and 'payment_url'
✅ payment_url is a valid HTTPS URL

POSSIBLE ERRORS:
❌ "ExPay request timed out" → Check internet connection
❌ "HTTP error" → Check API endpoint URL
❌ "Non-JSON response" → Check API credentials

STEP 2: Test check_order_status()
──────────────────────────────────
>>> # Use orderId from previous step
>>> status = client.check_order_status('1234561705047510')
>>> print(status)

EXPECTED OUTPUT:
✅ Dictionary with transaction status
✅ Contains: txnStatus, orderId, amount, etc.
✅ txnStatus is one of: SUCCESS, FAILED, PENDING, NOT_FOUND

For test order:
⚠️  Most likely returns "NOT_FOUND" (order wasn't processed)

STEP 3: Test Error Handling
─────────────────────────────
>>> # Test invalid amount
>>> try:
...     result = client.create_order(
...         customer_mobile='9000000000',
...         amount='-10',  # Invalid!
...         order_id='test',
...         remark1='test'
...     )
... except ExPayError as e:
...     print(f"Caught error: {e}")
...

EXPECTED:
✅ ExPayError is raised
✅ Error message is descriptive

STEP 4: Exit Django Shell
──────────────────────────
>>> exit()
"""

print(API_TESTING)

# ═══════════════════════════════════════════════════════════════════════════
# PART 4: PRODUCTION TESTING (WITH REAL PAYMENT)
# ═══════════════════════════════════════════════════════════════════════════

PRODUCTION_TESTING = """
═══════════════════════════════════════════════════════════════════════════
PART 4: PRODUCTION TESTING (WITH REAL PAYMENT)
═══════════════════════════════════════════════════════════════════════════

Purpose: Test end-to-end payment flow with real payment
Time: 15 minutes
Prerequisites: 
  - Code deployed to production
  - Webhook URL registered in ExPay dashboard
  - ExPay test cards available (check docs)

STEP 1: Prepare Test Environment
──────────────────────────────────
1. Create test user account on production
2. Verify can login to /accounts/login/
3. Check /shop/ loads products
4. Verify payment method options appear

STEP 2: Test Wallet Top-up Flow
────────────────────────────────
1. Navigate to /wallet/
2. Enter amount: 100
3. Select EXPAY as payment method
4. Click "Top-up"
5. Redirected to ExPay payment page
6. Use test card (ExPay provides test cards):
   Card: 4111111111111111
   Expiry: 12/25
   CVV: 123
7. Complete payment
8. Redirected back to your site
9. Check /wallet/:
   ✅ Balance updated with 100 (or equivalent)
   ✅ Transaction history shows top-up
10. Check admin (/hazumake-control/):
    ✅ Order created with status COMPLETED
    ✅ Transaction recorded

STEP 3: Check Webhook Logs
───────────────────────────
1. SSH into production server
2. Check Django error logs:
   tail -f /var/log/django/error.log
3. Look for: "ExPay webhook event=PAYMENT_SUCCESS"
4. Verify signature verification passed
5. Verify no errors during order update

STEP 4: Test Product Purchase Flow
────────────────────────────────────
1. Go to /shop/
2. Select a product (game top-up)
3. Enter player ID and zone ID
4. Select EXPAY as payment method
5. Click "Buy"
6. Complete payment using test card
7. Redirected back to site
8. Check /orders/:
   ✅ Order shows status COMPLETED
   ✅ Smile.one fulfillment triggered (check fulfillment status)
9. Check admin:
   ✅ Order has payment_transaction_id set
   ✅ Payment status is PAID

STEP 5: Test Failed Payment
────────────────────────────
1. Repeat wallet top-up flow
2. Use ExPay test card that fails (if available)
   OR close payment page without completing
3. Check order status:
   ✅ Order marked as FAILED
   ✅ Wallet NOT credited
   ✅ Transaction NOT created

STEP 6: Monitor for 24 Hours
──────────────────────────────
After initial tests, monitor:
  - Django error logs for any exceptions
  - ExPay dashboard for webhook delivery status
  - Admin panel for failed orders
  - Wallet for fraudulent transactions
  - Payment success rates

EXPECTED SUCCESS RATE: > 95%
If lower, investigate webhook failures.
"""

print(PRODUCTION_TESTING)

# ═══════════════════════════════════════════════════════════════════════════
# PART 5: TROUBLESHOOTING
# ═══════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING = """
═══════════════════════════════════════════════════════════════════════════
PART 5: TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════

PROBLEM: "ModuleNotFoundError: No module named 'services'"
SOLUTION:
  - Verify hazu/services/ directory exists
  - Verify hazu/services/__init__.py exists (empty file)
  - Verify hazu/services/payments/ directory exists
  - Run: python manage.py shell -c "from services.payments.expay_api import get_client; print('OK')"
  - Check if running Django from correct directory (hazu/)

PROBLEM: "ExPay API call timed out"
SOLUTION:
  - Check internet connection
  - Verify ExPay API is accessible: ping exgateway2.in (or curl check)
  - Check firewall allows outbound HTTPS
  - Increase timeout in expay_api.py if needed (default 15s)
  - Check ExPay status page for API downtime

PROBLEM: "Webhook signature verification failed"
SOLUTION:
  - Verify EXPAY_WEBHOOK_SECRET matches ExPay dashboard value exactly
  - Check raw request body (not parsed JSON)
  - Verify X-ExPay-Timestamp header is present
  - Verify X-ExPay-Signature header is present
  - Check if running Django from correct directory
  - Use ngrok to test locally before production

PROBLEM: "Order not found when webhook is called"
SOLUTION:
  - Webhook creates order AFTER user leaves payment page
  - For test webhook, this is normal (order doesn't exist)
  - Order must be created with smile_order_id that matches ExPay orderId
  - Check if Order is being stored correctly before payment
  - Verify Order.smile_order_id matches orderId from ExPay

PROBLEM: "Payment succeeds but wallet not credited"
SOLUTION:
  - Check webhook was called (look for log message)
  - Check webhook signature verification passed
  - Check _mark_order_completed() is being executed
  - Verify wallet.balance += amount is working
  - Check if Transaction is created in database
  - Review Admin → Wallet → check balance was updated

PROBLEM: "200 response not being returned"
SOLUTION:
  - Verify ExPayWebhookView returns JsonResponse(..., status=200)
  - Check for exceptions in _mark_order_completed()
  - Check for exceptions in _verify_signature()
  - Add try-except around order lookup
  - Always return HTTP 200 (even if errors occur)

PROBLEM: "ExPay test webhook fails in production"
SOLUTION:
  - Verify webhook URL is accessible: curl https://hazumakestore.com/api/wallet/webhook/
  - Should get POST method error (404/405), not timeout
  - Check EXPAY_WEBHOOK_SECRET is set in production .env
  - Verify URL matches exactly in ExPay dashboard
  - Check Django logs (tail -f) while sending test webhook
  - Verify nginx/apache forwarding is configured correctly

PROBLEM: "Duplicate orders created for single payment"
SOLUTION:
  - Webhook may be called multiple times
  - Implement idempotency check using payment_transaction_id
  - Use: Order.objects.get_or_create(payment_transaction_id=...)
  - Add database-level unique constraint
  - Check ExPay webhook retry settings

DEBUG CHECKLIST:
────────────────
☐ 1. Check Django console for errors (python manage.py runserver)
☐ 2. Check production logs (tail -f /var/log/django/error.log)
☐ 3. Search logs for "ExPay" to find all payment events
☐ 4. Check .env has correct EXPAY_* values
☐ 5. Check settings.py loads .env correctly
☐ 6. Test ExPayAPI directly in Django shell
☐ 7. Verify webhook URL is publicly accessible
☐ 8. Test webhook with ngrok locally first
☐ 9. Check ExPay dashboard for webhook history
☐ 10. Verify Order/Wallet updated in admin
"""

print(TROUBLESHOOTING)

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

print("""
═══════════════════════════════════════════════════════════════════════════
TESTING SUMMARY
═══════════════════════════════════════════════════════════════════════════

QUICK TEST CHECKLIST:

☐ PART 1: Local Testing (30 min)
  ✅ Django imports work
  ✅ Payment method appears in UI
  ✅ Form submission reaches backend
  ✅ No 500 errors

☐ PART 2: Webhook Testing (20 min)
  ✅ ngrok tunnel working
  ✅ ExPay webhook URL registered
  ✅ Test webhook received
  ✅ Signature verification passed
  ✅ HTTP 200 response sent

☐ PART 3: API Testing (15 min)
  ✅ create_order() returns valid response
  ✅ check_order_status() works
  ✅ Error handling catches exceptions

☐ PART 4: Production Testing (15 min)
  ✅ Wallet top-up completes end-to-end
  ✅ Balance updated correctly
  ✅ Product purchase completes
  ✅ Smile.one fulfillment triggered

TOTAL TIME: ~90 minutes
CONFIDENCE: High ✅

If all tests pass: READY FOR PRODUCTION ✅
If any test fails: Review TROUBLESHOOTING section
═══════════════════════════════════════════════════════════════════════════
""")
