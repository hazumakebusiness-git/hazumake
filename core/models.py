from django.db import models


class PageBackground(models.Model):
    BACKGROUND_TYPES = (
        ('color', 'Color'),
        ('image', 'Image'),
    )

    page_identifier = models.CharField(max_length=100, unique=True, help_text='Example: home, shop, login, dashboard')
    background_type = models.CharField(max_length=10, choices=BACKGROUND_TYPES, default='color')
    background_color = models.CharField(max_length=7, blank=True, help_text='Hex color, e.g. #1f2937')
    background_image = models.ImageField(upload_to='backgrounds/page/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Page Background'
        verbose_name_plural = 'Page Backgrounds'
        ordering = ['page_identifier']

    def __str__(self):
        return self.page_identifier


class SiteSettings(models.Model):
    # Singleton model — only one row ever exists
    store_manager_name = models.CharField(max_length=100, default='Store Manager')
    store_manager_phone = models.CharField(max_length=20, default='9612026834')
    store_manager_whatsapp = models.CharField(max_length=20, blank=True,
        help_text='WhatsApp number with country code e.g. 919612026834')
    # --- ADD THESE NEW FIELDS ---
    home_bg     = models.ImageField(upload_to='backgrounds/', blank=True, null=True, verbose_name='Home Background')
    shop_bg     = models.ImageField(upload_to='backgrounds/', blank=True, null=True, verbose_name='Shop Page Background')
    game_shop_bg   = models.ImageField(upload_to='backgrounds/', blank=True, null=True, verbose_name='Game Shop Background')
    product_bg  = models.ImageField(upload_to='backgrounds/', blank=True, null=True, verbose_name='Product Detail Background')
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        # Enforce singleton
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        try:
            obj, _ = cls.objects.get_or_create(pk=1, defaults={
                'store_manager_name': 'Store Manager',
                'store_manager_phone': '9612026834',
                'store_manager_whatsapp': '919612026834',
            })
            return obj
        except Exception:
            # Return a dummy object if database is not ready
            return cls(
                store_manager_name='Adish Meetei',
                store_manager_phone='+919612026834',
                store_manager_whatsapp='+919612026834'
            )
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"{self.name} — {self.subject} ({self.created_at.strftime('%d %b %Y')})"