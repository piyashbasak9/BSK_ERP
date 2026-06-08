from django.contrib import admin
from .models import LoanProduct, LoanApplication, LoanDisbursement, LoanInstallmentSchedule

@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'interest_rate', 'min_amount', 'max_amount', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['is_active', 'installment_frequency']

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['member', 'product', 'applied_amount', 'status', 'applied_date']
    list_filter = ['status', 'applied_date']
    search_fields = ['member__name', 'member__member_id']

@admin.register(LoanDisbursement)
class LoanDisbursementAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount', 'disbursement_date', 'method']
    list_filter = ['disbursement_date', 'method']

@admin.register(LoanInstallmentSchedule)
class LoanInstallmentScheduleAdmin(admin.ModelAdmin):
    list_display = ['loan', 'installment_no', 'due_date', 'total_due', 'is_paid']
    list_filter = ['is_paid', 'due_date']