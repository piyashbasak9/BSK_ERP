from django.contrib import admin
from .models import LoanProduct, LoanApplication, LoanDisbursement, LoanInstallmentSchedule

admin.site.register((LoanProduct, LoanApplication, LoanDisbursement, LoanInstallmentSchedule))
