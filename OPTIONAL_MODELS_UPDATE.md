"""
OPTIONAL_MODELS_UPDATE.md

Optional database schema improvements for ExPay integration
===========================================================
"""

# ═══════════════════════════════════════════════════════════════════════════
# OPTION 1: Add payment_transaction_id to Order (RECOMMENDED)
# ═══════════════════════════════════════════════════════════════════════════

"""
This adds a field to track the payment gateway's transaction ID,
making it easier to reconcile payments and debug issues.

File: orders/models.py

Add this field to the Order model:
"""

OPTION_1_CODE = """
class Order(models.Model):
    # ... existing fields ...
    
    # Payment tracking fields
    smile_order_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Smile.one fulfillment order ID"
    )
    
    # NEW: Payment gateway transaction tracking
    payment_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Payment gateway transaction ID (ExPay orderId, Razorpay order_id, etc.)"
    )
    
    # ... rest of model ...
    
    class Meta:
        # ... existing meta ...
        indexes = [
            models.Index(fields=['smile_order_id']),
            models.Index(fields=['payment_transaction_id']),
            models.Index(fields=['user', 'created_at']),
        ]
"""

print("OPTION 1 - Add payment_transaction_id")
print("=" * 80)
print(OPTION_1_CODE)

# ═══════════════════════════════════════════════════════════════════════════
# MIGRATION STEPS
# ═══════════════════════════════════════════════════════════════════════════

MIGRATION_STEPS = """
STEP 1: Update orders/models.py
────────────────────────────────
Add the payment_transaction_id field (see code above)

STEP 2: Create migration
────────────────────────
python manage.py makemigrations orders

This will create: orders/migrations/000X_add_payment_transaction_id.py

STEP 3: Review migration
──────────────────────────
Edit the migration file to ensure it looks correct:
  - Field type: CharField
  - max_length: 100
  - blank: True
  - null: True
  - db_index: True (for fast lookups)

STEP 4: Apply migration
───────────────────────
# Locally:
python manage.py migrate

# Production (if using separate database):
python manage.py migrate --database=production

STEP 5: Update payments/views.py webhook
────────────────────────────────────────
In payments/views.py, update the webhook to store the transaction ID:

CURRENT CODE:
    order = Order.objects.get(smile_order_id=order_id)

UPDATED CODE:
    order = Order.objects.get(smile_order_id=order_id)
    order.payment_transaction_id = order_id  # NEW: Store ExPay orderId
    order.save()

Or, update the lookup to use payment_transaction_id:
    order = Order.objects.get(payment_transaction_id=order_id)
"""

print("\n" + "=" * 80)
print("MIGRATION STEPS")
print("=" * 80)
print(MIGRATION_STEPS)

# ═══════════════════════════════════════════════════════════════════════════
# OPTION 2: Create WalletTopup model (ADVANCED)
# ═══════════════════════════════════════════════════════════════════════════

"""
If you want to track wallet top-ups separately from product purchases,
create a dedicated WalletTopup model.

This is optional but useful for:
  - Reporting on top-up trends
  - Auditing wallet transactions
  - Separate reconciliation from product sales
"""

OPTION_2_CODE = """
# File: wallet/models.py

from django.db import models
from django.conf import settings
import uuid

class WalletTopup(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('RAZORPAY', 'Razorpay'),
        ('EXPAY', 'ExPay'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet_topups'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="ExPay orderId or payment gateway transaction ID"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['payment_transaction_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"₹{self.amount} top-up by {self.user.email} ({self.status})"
    
    def mark_completed(self):
        from django.utils import timezone
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self):
        self.status = 'FAILED'
        self.save()
"""

print("\n" + "=" * 80)
print("OPTION 2 - Create WalletTopup model (Advanced)")
print("=" * 80)
print(OPTION_2_CODE)

# ═══════════════════════════════════════════════════════════════════════════
# OPTION 3: Update webhook to use WalletTopup
# ═══════════════════════════════════════════════════════════════════════════

OPTION_3_CODE = """
# In payments/views.py, update _mark_order_completed() to handle WalletTopup

@staticmethod
def _mark_order_completed(order, utr, amount):
    '''Mark order as completed and credit user's wallet.'''
    
    from wallet.models import WalletTopup
    
    # Check if this is a wallet top-up
    try:
        wallet_topup = WalletTopup.objects.get(
            payment_transaction_id=order.payment_transaction_id
        )
        # Update wallet topup status
        wallet_topup.mark_completed()
        
        # Credit wallet
        wallet = order.user.wallet
        wallet.balance += wallet_topup.amount
        wallet.save()
        
        # Record transaction
        Transaction.objects.create(
            wallet=wallet,
            type='CREDIT',
            amount=wallet_topup.amount,
            balance_after=wallet.balance,
            note=f"Wallet top-up via ExPay (UTR: {utr})"
        )
    except WalletTopup.DoesNotExist:
        # Not a wallet top-up, skip
        pass
    
    # Mark order as completed
    order.status = 'COMPLETED'
    order.save()
"""

print("\n" + "=" * 80)
print("OPTION 3 - Update webhook for WalletTopup")
print("=" * 80)
print(OPTION_3_CODE)

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE INDEX PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════

DATABASE_INDEXES = """
WHY INDEXES?
─────────────
Indexes speed up database queries. Important for:
  - Webhook lookups by payment_transaction_id (fast lookup)
  - Admin filtering by status
  - Payment reports and reconciliation
  - User transaction history

RECOMMENDED INDEXES
──────────────────
1. Order:
   - payment_transaction_id (for webhook fast lookup)
   - smile_order_id (for Smile.one fulfillment tracking)
   - user + created_at (for user order history)

2. WalletTopup (if used):
   - payment_transaction_id (for webhook fast lookup)
   - user + created_at (for user's topup history)
   - status (for filtering pending/completed)

3. Transaction:
   - wallet (for wallet transaction history)
   - created_at (for recent transactions)

Django automatically creates indexes on:
  - Primary keys (id)
  - Foreign keys (user, wallet, etc.)
  - Fields with db_index=True
"""

print("\n" + "=" * 80)
print("DATABASE INDEX PERFORMANCE")
print("=" * 80)
print(DATABASE_INDEXES)

# ═══════════════════════════════════════════════════════════════════════════
# ADMIN INTERFACE IMPROVEMENTS
# ═══════════════════════════════════════════════════════════════════════════

ADMIN_IMPROVEMENTS = """
Update orders/admin.py to show payment_transaction_id:

from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'product',
        'status',
        'payment_method',
        'payment_transaction_id',  # NEW
        'smile_order_id',
        'created_at',
    )
    
    list_filter = (
        'status',
        'payment_method',
        'created_at',
    )
    
    search_fields = (
        'user__email',
        'product__name',
        'payment_transaction_id',  # NEW
        'smile_order_id',
    )
    
    readonly_fields = (
        'id',
        'created_at',
        'payment_transaction_id',  # NEW
    )
    
    fieldsets = (
        ('User Info', {
            'fields': ('id', 'user', 'created_at'),
        }),
        ('Product', {
            'fields': ('product', 'game', 'quantity'),
        }),
        ('Player Info', {
            'fields': ('player_uid', 'player_sid', 'player_fields'),
        }),
        ('Payment', {
            'fields': (
                'payment_method',
                'payment_transaction_id',  # NEW
                'payment_status',
            ),
        }),
        ('Order Status', {
            'fields': ('status', 'smile_order_id'),
        }),
        ('Financial', {
            'fields': ('total_coins', 'total_inr'),
        }),
    )
"""

print("\n" + "=" * 80)
print("ADMIN INTERFACE IMPROVEMENTS")
print("=" * 80)
print(ADMIN_IMPROVEMENTS)

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
OPTION 1: Add payment_transaction_id to Order
✅ Recommended | Easy (5 minutes) | Useful (payment tracking)

OPTION 2: Create WalletTopup model
⚠️  Advanced | Medium (15 minutes) | Nice to have (separate tracking)

OPTION 3: Update admin interface
✅ Recommended | Easy (5 minutes) | Useful (visibility)

MINIMUM REQUIRED: None (already works without)
RECOMMENDED: Option 1 + Option 3 (10 minutes)
ADVANCED: Option 1 + Option 2 + Option 3 (30 minutes)

DEFAULT: Skip for now, implement later if needed
""")
