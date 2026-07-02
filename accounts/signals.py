from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser
from wallet.models import Wallet

@receiver(post_save, sender=CustomUser)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
    else:
        Wallet.objects.get_or_create(user=instance)


# Handle Google OAuth login - auto-verify email
def social_account_added_handler(sender, request, sociallogin, **kwargs):
    """Auto-verify email for Google OAuth users."""
    user = sociallogin.user
    if sociallogin.account.provider == 'google':
        user.is_email_verified = True
        user.is_active = True
        user.save()

# Register the signal handler
try:
    from allauth.socialaccount.signals import social_account_added
    social_account_added.connect(social_account_added_handler)
except ImportError:
    pass