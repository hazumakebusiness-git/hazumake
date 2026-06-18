"""
DEPLOYMENT_CHECKLIST.md

Step-by-step checklist for ExPay payment gateway migration
===========================================================
"""

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: BACKEND SETUP (COMPLETED ✅)
# ═══════════════════════════════════════════════════════════════════════════

PHASE_1_ITEMS = [
    "✅ Created hazu/services/payments/expay_api.py (ExPayAPI client)",
    "✅ Created hazu/payments/ app with views, urls, apps",
    "✅ Added ExPayWebhookView with HMAC signature verification",
    "✅ Updated settings.py with EXPAY_USER_TOKEN, EXPAY_WEBHOOK_SECRET",
    "✅ Updated .env with ExPay credentials",
    "✅ Added payments app to INSTALLED_APPS",
    "✅ Added webhook URL route in hazu/urls.py",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: VIEW INTEGRATION (MANUAL - Follow code snippets)
# ═══════════════════════════════════════════════════════════════════════════

PHASE_2_ITEMS = [
    "☐ wallet/views.py: Replace razorpay_create_order with expay_create_order",
    "☐ wallet/urls.py: Update path to point to expay_create_order",
    "☐ orders/views.py: Add EXPAY payment method case to place_order()",
    "☐ orders/views.py: Import get_expay_client, ExPayError, time",
    "☐ Verify all imports are at top of files",
    "☐ Test locally: python manage.py runserver",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: FRONTEND UPDATES (MANUAL - Update templates)
# ═══════════════════════════════════════════════════════════════════════════

PHASE_3_ITEMS = [
    "☐ Add EXPAY radio button to payment method selection",
    "☐ Update checkout JavaScript to handle EXPAY payment method",
    "☐ For EXPAY: redirect to payment_url instead of opening modal",
    "☐ For RAZORPAY: keep existing Razorpay modal code",
    "☐ Test form submission with each payment method",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: DATABASE (OPTIONAL but recommended)
# ═══════════════════════════════════════════════════════════════════════════

PHASE_4_ITEMS = [
    "☐ orders/models.py: Add payment_transaction_id field (optional)",
    "☐ Run: python manage.py makemigrations orders",
    "☐ Run: python manage.py migrate",
    "☐ Update webhook to store payment_transaction_id (optional)",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 5: LOCAL TESTING
# ═══════════════════════════════════════════════════════════════════════════

PHASE_5_ITEMS = [
    "☐ Start Django: python manage.py runserver",
    "☐ Login to test account at http://localhost:8000/accounts/login/",
    "☐ Navigate to /wallet/ for wallet top-up",
    "☐ SKIP payment for now (test flow only)",
    "☐ Navigate to /shop/ and select a product",
    "☐ Test with each payment method (WALLET, RAZORPAY, EXPAY)",
    "☐ Verify form posts correctly to backend",
    "☐ Check Django console for any errors",
    "☐ Install ngrok: pip install ngrok or download from ngrok.com",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 6: WEBHOOK TESTING (LOCAL)
# ═══════════════════════════════════════════════════════════════════════════

PHASE_6_ITEMS = [
    "☐ Open new terminal and run: ngrok http 8000",
    "☐ Copy the https://xxxxx.ngrok.io URL",
    "☐ In ExPay Dashboard → Webhook Settings:",
    "☐   Set URL: https://xxxxx.ngrok.io/api/wallet/webhook/",
    "☐   Save settings",
    "☐ In ExPay Dashboard: Click 'Send Test Webhook'",
    "☐ Check Django console for: 'ExPay webhook event=...'",
    "☐ Verify HTTP 200 response is returned",
    "☐ Verify signature verification passed (check logs)",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 7: PRODUCTION PREPARATION
# ═══════════════════════════════════════════════════════════════════════════

PHASE_7_ITEMS = [
    "☐ Review all EXPAY_*.md documentation files",
    "☐ Review webhook signature verification logic",
    "☐ Review error handling and logging",
    "☐ Test payment flow end-to-end locally",
    "☐ Verify Order is created with correct status",
    "☐ Verify Wallet is credited (if applicable)",
    "☐ Check logs for any warnings or errors",
    "☐ Create backup of database",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 8: PRODUCTION DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════════════

PHASE_8_ITEMS = [
    "☐ Commit code: git add -A && git commit -m 'Integrate ExPay payment gateway'",
    "☐ Push to repository: git push origin master",
    "☐ Deploy to production server",
    "☐ Verify services/payments/ directory exists on server",
    "☐ Verify payments/ app is deployed",
    "☐ Verify Django can import: from services.payments.expay_api import get_client",
    "☐ Run migrations: python manage.py migrate",
    "☐ Collect static files: python manage.py collectstatic --noinput",
    "☐ Restart Django app (uwsgi, gunicorn, etc.)",
    "☐ Restart web server (nginx, apache, etc.)",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 9: PRODUCTION WEBHOOK REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════

PHASE_9_ITEMS = [
    "☐ In ExPay Dashboard → Webhook Settings:",
    "☐   Set URL: https://hazumakestore.com/api/wallet/webhook/",
    "☐   Set Secret: from .env EXPAY_WEBHOOK_SECRET",
    "☐   Enable webhook deliveries",
    "☐   Save settings",
    "☐ In ExPay Dashboard: Click 'Send Test Webhook'",
    "☐ Check production logs for webhook processing",
    "☐ Verify HTTP 200 response from webhook",
    "☐ Verify Order status updated in admin",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 10: PRODUCTION TESTING
# ═══════════════════════════════════════════════════════════════════════════

PHASE_10_ITEMS = [
    "☐ Login to production site",
    "☐ Test wallet top-up flow with EXPAY",
    "☐ Complete actual payment (use test card if available)",
    "☐ Verify Order created in /hazumake-control/",
    "☐ Verify wallet balance updated",
    "☐ Verify webhook was called (check logs)",
    "☐ Test product purchase flow with EXPAY",
    "☐ Complete payment and verify delivery (Smile.one fulfillment)",
    "☐ Test error scenarios:",
    "☐   - Insufficient wallet balance",
    "☐   - Invalid product",
    "☐   - Payment declined",
    "☐ Monitor logs for any issues: tail -f /var/log/django/error.log",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 11: CLEANUP & OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════

PHASE_11_ITEMS = [
    "☐ Remove old KhilaadiXPro SDK files (if any exist)",
    "☐ Remove old Flask webhook.py (if exists)",
    "☐ Remove Razorpay SDK from requirements if no longer used",
    "☐ Update docs/README.md with new payment gateway info",
    "☐ Remove DEBUG print statements from views",
    "☐ Verify no hardcoded credentials in code",
    "☐ Review error messages for user-friendliness",
    "☐ Test mobile responsive payment flow",
]

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 12: MONITORING & MAINTENANCE
# ═══════════════════════════════════════════════════════════════════════════

PHASE_12_ITEMS = [
    "☐ Set up logging for webhook events",
    "☐ Monitor failed payments in logs",
    "☐ Create alert for webhook signature verification failures",
    "☐ Document troubleshooting steps for common issues",
    "☐ Schedule weekly review of payment logs",
    "☐ Keep ExPay dashboard monitored for issues",
    "☐ Test webhook retry mechanism (ExPay will retry on HTTP error)",
    "☐ Document contact info for ExPay support",
]

# ═══════════════════════════════════════════════════════════════════════════
# TROUBLESHOOTING GUIDE
# ═══════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING = """
PROBLEM: ExPay order creation fails with "connection timeout"
SOLUTION:
  - Verify settings.py has correct EXPAY_USER_TOKEN
  - Check if base URL is correct: https://exgateway2.in/api
  - Verify internet connection from server
  - Check firewall rules allow outbound HTTPS

PROBLEM: Webhook signature verification fails
SOLUTION:
  - Verify EXPAY_WEBHOOK_SECRET in .env matches ExPay dashboard
  - Check raw request body (signature must be on original bytes)
  - Verify timestamp header is not manipulated
  - Check logs for exact signature and expected values

PROBLEM: Order not found when webhook is received
SOLUTION:
  - Verify Order is created BEFORE user leaves for payment
  - Check if smile_order_id is being set correctly
  - Verify webhook is looking up Order correctly
  - Check Order.objects.filter(smile_order_id=...) in Django shell

PROBLEM: Wallet not credited after payment
SOLUTION:
  - Verify webhook received the PAYMENT_SUCCESS event
  - Check _mark_order_completed() function in webhook handler
  - Verify wallet.balance update is called
  - Check Transaction is created in wallet_transactions

PROBLEM: Payment URL not working
SOLUTION:
  - Verify ExPayAPI.create_order() returned payment_url
  - Check if URL is being passed correctly to frontend
  - Verify frontend is redirecting (not opening in new tab)
  - Check browser console for JavaScript errors

PROBLEM: Duplicate orders created
SOLUTION:
  - Webhook may be retrying; check if X-ExPay-Delivery header is unique
  - Implement idempotency check using payment_transaction_id
  - Verify Order creation is wrapped in database transaction
  - Use select_for_update() to prevent race conditions

PROBLEM: Tests failing
SOLUTION:
  - Verify test database has correct settings
  - Mock ExPayAPI.create_order() in unit tests
  - Check if ngrok URL changed (restart ngrok if using)
  - Verify Django log level includes INFO (for debug logging)
"""

print(TROUBLESHOOTING)

# ═══════════════════════════════════════════════════════════════════════════
# QUICK START
# ═══════════════════════════════════════════════════════════════════════════

print("""
═══════════════════════════════════════════════════════════════════════════
QUICK START SUMMARY
═══════════════════════════════════════════════════════════════════════════

1. Backend is READY ✅
   - ExPay API client created
   - Webhook handler created
   - Settings configured
   - URL routing configured

2. DO THIS NEXT (manual):
   a) Update wallet/views.py (replace razorpay_create_order)
   b) Update orders/views.py (add EXPAY payment method)
   c) Update frontend templates (add EXPAY radio button)
   d) Update checkout JavaScript (handle EXPAY redirect)

3. TESTING:
   a) Test locally: python manage.py runserver
   b) Test webhook with ngrok
   c) Test with test cards in ExPay

4. DEPLOY:
   a) Commit and push code
   b) Deploy to production
   c) Register webhook URL in ExPay dashboard
   d) Run migrations: python manage.py migrate
   e) Test end-to-end

5. MONITOR:
   a) Check logs for any errors
   b) Monitor failed payments
   c) Verify orders are creating correctly

See EXPAY_CODE_SNIPPETS.md for exact code to copy-paste!
═══════════════════════════════════════════════════════════════════════════
""")
