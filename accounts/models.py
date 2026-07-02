from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractUser



# Create your models here.
class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use email as primary login identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Required by AbstractUser, auto-generated from email

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Auto-generate username from email if not set
        if not self.username:
            base = self.email.split('@')[0][:120]
            self.username = base or 'user'
        super().save(*args, **kwargs)


class OTPCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    identifier = models.CharField(max_length=255)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['identifier', 'is_used', 'expires_at', 'created_at']),
        ]

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()
    
