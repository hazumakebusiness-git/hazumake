from django.contrib import admin
from .models import Order

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'total_inr', 'status', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('user__email', 'product__name')
