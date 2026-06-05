from django.db import models
from apps.branches.models import Branch
from apps.members.models import Member

class SavingsProduct(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    min_balance = models.DecimalField(max_digits=12, decimal_places=2)
    service_charge = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class SavingsAccount(models.Model):
    account_no = models.CharField(max_length=50, unique=True)
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    product = models.ForeignKey(SavingsProduct, on_delete=models.PROTECT)
    opening_date = models.DateField()
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.account_no

class SavingsTransaction(models.Model):
    TRANSACTION_TYPES = [('DEPOSIT', 'Deposit'), ('WITHDRAWAL', 'Withdrawal'), ('INTEREST', 'Interest'), ('CHARGE', 'Charge')]
    account = models.ForeignKey(SavingsAccount, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)