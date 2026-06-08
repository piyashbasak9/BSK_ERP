from django.db import models
from apps.branches.models import Branch
from apps.members.models import Member
from decimal import Decimal


class SavingsProduct(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate (%)")
    min_balance = models.DecimalField(max_digits=12, decimal_places=2, help_text="Minimum balance required")
    service_charge = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Monthly service charge")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class SavingsAccount(models.Model):
    account_no = models.CharField(max_length=50, unique=True)
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    product = models.ForeignKey(SavingsProduct, on_delete=models.PROTECT)
    opening_date = models.DateField()
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    closed_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.account_no

    def save(self, *args, **kwargs):
        if not self.account_no:
            # Auto-generate account number: 'SAV' + year + month + 6-digit sequence
            from django.utils import timezone
            year = timezone.now().strftime('%y')
            month = timezone.now().strftime('%m')
            last = SavingsAccount.objects.filter(account_no__startswith=f'SAV{year}{month}').order_by('id').last()
            if last:
                seq = int(last.account_no[-6:]) + 1
            else:
                seq = 1
            self.account_no = f'SAV{year}{month}{seq:06d}'
        super().save(*args, **kwargs)


class SavingsTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('INTEREST', 'Interest'),
        ('CHARGE', 'Service Charge'),
        ('REVERSAL', 'Reversal')
    ]
    account = models.ForeignKey(SavingsAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)
    reversed_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reversed_transactions')
    reversed_at = models.DateTimeField(null=True, blank=True)
    is_reversed = models.BooleanField(default=False)
    original_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reversal_transaction')

    def __str__(self):
        return f"{self.date} - {self.account.account_no} - {self.transaction_type} - {self.amount}"