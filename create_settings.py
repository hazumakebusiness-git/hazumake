import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hazu.settings')
django.setup()

from core.models import SiteSettings

# Create SiteSettings if it doesn't exist
if not SiteSettings.objects.exists():
    SiteSettings.objects.create(
        store_manager_name='Adish Meetei',
        store_manager_phone='+919612026834',
        store_manager_whatsapp='+919612026834'
    )
    print("SiteSettings created successfully!")
else:
    print("SiteSettings already exists.")