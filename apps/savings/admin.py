from django.contrib import admin
from .models import SavingsProduct, SavingsAccount, SavingsTransaction

@admin.register(SavingsProduct)
class SavingsProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'interest_rate', 'min_balance', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['is_active']

@admin.register(SavingsAccount)
class SavingsAccountAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'member', 'product', 'current_balance', 'is_active', 'is_deleted']
    search_fields = ['account_no', 'member__name']
    list_filter = ['is_active', 'is_deleted', 'product']

@admin.register(SavingsTransaction)
class SavingsTransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'account', 'transaction_type', 'amount', 'balance_after', 'is_reversed']
    list_filter = ['transaction_type', 'is_reversed', 'date']
    search_fields = ['account__account_no', 'description']