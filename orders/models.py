from django.db import models
import uuid
from django.conf import settings

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )

    PAYMENT_CHOICES = (
        ('WALLET', 'Wallet'),
        ('RAZORPAY', 'Razorpay'),
        ('EXPAY', 'ExPay'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='orders')
    game = models.ForeignKey('products.Game', on_delete=models.PROTECT, null=True)
    smile_product_id = models.CharField(max_length=20, null=True, blank=True)
    smile_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text='Payment gateway transaction ID (ExPay orderId, Razorpay order_id, etc.)'
    )
    player_uid = models.CharField(max_length=50, default='', blank=False)
    player_sid = models.CharField(max_length=50, blank=True, default='')
    quantity = models.PositiveIntegerField(default=1)
    player_fields = models.JSONField(default=dict)
    total_coins = models.IntegerField()
    total_inr = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.product:
            if not self.game:
                self.game = self.product.game
            if not self.smile_product_id:
                self.smile_product_id = self.product.smile_product_id
            if not self.total_coins:
                self.total_coins = self.product.price_coins * self.quantity
            if not self.total_inr:
                self.total_inr = self.product.price_inr * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.id} - {self.user.email} - {self.product.name} [{self.status}]"
