from django.db import models

class SiteSettings(models.Model):
    # Singleton model — only one row ever exists
    store_manager_name = models.CharField(max_length=100, default='Store Manager')
    store_manager_phone = models.CharField(max_length=20, default='9612026834')
    store_manager_whatsapp = models.CharField(max_length=20, blank=True,
        help_text='WhatsApp number with country code e.g. 919612026834')

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