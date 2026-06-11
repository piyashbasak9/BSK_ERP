from django.contrib import admin
from .models import DailyCollectionSheet, CollectionEntry

@admin.register(DailyCollectionSheet)
class DailyCollectionSheetAdmin(admin.ModelAdmin):
    list_display = ['date', 'branch', 'collector', 'total_cash', 'verified']
    list_filter = ['verified', 'branch', 'date']
    search_fields = ['branch__name', 'collector__username']
    readonly_fields = ['total_cash', 'verified_by', 'verified_at']

@admin.register(CollectionEntry)
class CollectionEntryAdmin(admin.ModelAdmin):
    list_display = ['sheet', 'member', 'collection_type', 'amount']
    list_filter = ['collection_type', 'sheet__branch']
    search_fields = ['member__name', 'sheet__date']