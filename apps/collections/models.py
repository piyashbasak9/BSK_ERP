from django.db import models
from apps.branches.models import Branch
from apps.members.models import Member
from apps.loans.models import LoanInstallmentSchedule
from apps.savings.models import SavingsAccount

class DailyCollectionSheet(models.Model):
    date = models.DateField()
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    collector = models.ForeignKey('authentication.User', on_delete=models.PROTECT)
    total_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, related_name='verified_sheets')

class CollectionEntry(models.Model):
    TYPE_CHOICES = [('loan', 'Loan Installment'), ('savings', 'Savings Deposit'), ('fee', 'Processing Fee')]
    sheet = models.ForeignKey(DailyCollectionSheet, on_delete=models.CASCADE, related_name='entries')
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    collection_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    loan_installment = models.ForeignKey(LoanInstallmentSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    savings_account = models.ForeignKey(SavingsAccount, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    principal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remark = models.TextField(blank=True)