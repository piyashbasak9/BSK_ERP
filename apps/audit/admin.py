from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'action', 'resource', 'resource_id', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['username', 'resource', 'ip_address']
    readonly_fields = ['timestamp']