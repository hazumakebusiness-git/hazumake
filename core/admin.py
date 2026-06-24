from django.contrib import admin
from .models import SiteSettings, ContactMessage

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Store Manager Contact', {
            'description': 'This number appears publicly on the Contact page.',
            'fields': ('store_manager_name', 'store_manager_phone', 'store_manager_whatsapp')
        }),
        ('Page Backgrounds', {             # <-- just add this second block
            'description': 'Upload a background image per page. Leave blank to use the default gradient.',
            'fields': ('home_bg', 'shop_bg', 'game_shop_bg', 'product_bg')
        }),                                # <-- comma after every block except the last
    )
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    list_editable = ('is_read',)

    def has_add_permission(self, request):
        return False