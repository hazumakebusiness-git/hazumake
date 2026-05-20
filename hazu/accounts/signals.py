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