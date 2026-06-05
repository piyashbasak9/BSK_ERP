from django.db import models
from apps.branches.models import Branch

class Account(models.Model):
    ACCOUNT_TYPES = [('Asset', 'Asset'), ('Liability', 'Liability'), ('Equity', 'Equity'), ('Income', 'Income'), ('Expense', 'Expense')]
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class JournalEntry(models.Model):
    voucher_no = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    description = models.TextField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_posted = models.BooleanField(default=True)

class JournalItem(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='items')
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    reference_no = models.CharField(max_length=100, blank=True)