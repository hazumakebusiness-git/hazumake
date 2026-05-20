from django.contrib import admin
from .models import Wallet, Transaction
# Register your models here.
@admin.register(Wallet)
class ProductWallet(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency')
    search_fields = ('user',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'type', 'amount', 'balance_after', 'created_at')
    list_filter = ('type',)
    search_fields = ('wallet__user__email',)


