from django.contrib import admin
from .models import Account, JournalEntry, JournalItem

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'parent', 'is_active', 'branch']
    list_filter = ['account_type', 'is_active', 'branch']
    search_fields = ['code', 'name']

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['voucher_no', 'date', 'description', 'branch', 'created_by', 'is_posted']
    list_filter = ['is_posted', 'branch', 'date']
    search_fields = ['voucher_no', 'description']
    readonly_fields = ['created_at']

@admin.register(JournalItem)
class JournalItemAdmin(admin.ModelAdmin):
    list_display = ['entry', 'account', 'debit', 'credit', 'reference_no']
    list_filter = ['entry__branch']
    search_fields = ['entry__voucher_no', 'account__code']