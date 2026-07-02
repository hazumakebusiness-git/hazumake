import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models

class Game(models.Model):
    FIELD_PRESETS = (
        ('MLBB', 'User ID + Zone ID'),
        ('BGMI', 'Player ID only'),
        ('FREEFIRE', 'UID only'),
        ('GENSHIN', 'UID + Server'),
        ('HONKAI', 'UID + Server'),
        ('CUSTOM', 'Custom fields'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)               # e.g. "Mobile Legends: Bang Bang"
    short_name = models.CharField(max_length=20, unique=True)  # e.g. "MLBB"
    slug = models.SlugField(unique=True)                  # e.g. "mobile-legends" — used in URLs
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='games/icons/', null=True, blank=True)
    banner = models.ImageField(upload_to='games/banners/', null=True, blank=True)
    field_preset = models.CharField(max_length=20, choices=FIELD_PRESETS, default='MLBB')
    
    # Dynamic checkout fields stored as JSON:
    # e.g. [{"name": "player_id", "label": "Player ID", "placeholder": "e.g. 123456789", "required": true},
    #        {"name": "zone_id", "label": "Zone ID", "placeholder": "e.g. 1234", "required": true}]
    checkout_fields = models.JSONField(default=list)
    
    # Smile.one / supplier config
    supplier_game_code = models.CharField(max_length=50, blank=True)  # code used in Smile.one API
    
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)      # shows on homepage
    sort_order = models.IntegerField(default=0)           # controls display order
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/shop/{self.slug}/"

class Product(models.Model):
    PRODUCT_TYPES = (
        ('DIAMOND', 'Diamonds'),
        ('STARLIGHT', 'Starlight Member'),
        ('BUNDLE', 'Bundles'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey('Game', on_delete=models.CASCADE, related_name='products', null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    smile_product_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='DIAMOND')
    diamond_amount = models.IntegerField(null=True, blank=True)
    price_brl = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_coins = models.IntegerField()
    price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    supplier_product_code = models.CharField(max_length=50, blank=True, null=True, help_text="Product code from Smile.one reseller catalog")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.price_brl is not None:
            self.price_inr = (Decimal(self.price_brl) * Decimal(str(settings.SMILE_BRL_TO_INR))).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.price_coins} Coins"