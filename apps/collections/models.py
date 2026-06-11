from django.db import models
from decimal import Decimal
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
    verified_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_sheets')
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.date} - {self.branch.name} - {self.collector.username}"

    def update_total_cash(self):
        """Recalculate total cash from all entries"""
        total = self.entries.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        if self.total_cash != total:
            self.total_cash = total
            self.save(update_fields=['total_cash'])
        return total

    def can_edit(self):
        return not self.verified

    class Meta:
        permissions = [
            ('can_verify_collectionsheet', 'Can verify collection sheets'),
        ]


class CollectionEntry(models.Model):
    TYPE_CHOICES = [
        ('loan', 'Loan Installment'),
        ('savings', 'Savings Deposit'),
        ('fee', 'Processing Fee')
    ]

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

    def __str__(self):
        return f"{self.sheet.date} - {self.member.name} - {self.amount}"

    def save(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            # If this is an update, we need to reverse the old effect first
            if self.pk:
                old = CollectionEntry.objects.get(pk=self.pk)
                self._reverse_effect(old)
            # Save the new state
            super().save(*args, **kwargs)
            # Apply the new effect (update loan/savings)
            self._apply_effect()
            # Update parent sheet total
            self.sheet.update_total_cash()

    def delete(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            # Reverse the effect before deleting the record
            self._reverse_effect(self)
            super().delete(*args, **kwargs)
            # Update parent sheet total
            self.sheet.update_total_cash()

    def _apply_effect(self):
        """Apply the collection effect to loan installment or savings account"""
        if self.collection_type == 'loan' and self.loan_installment:
            # Call the installment's make_payment method
            success, message = self.loan_installment.make_payment(self.amount, self.sheet.date)
            if not success:
                raise Exception(f"Loan payment failed: {message}")
        elif self.collection_type == 'savings' and self.savings_account:
            from apps.savings.models import SavingsTransaction
            # Create a deposit transaction
            new_balance = self.savings_account.current_balance + self.amount
            SavingsTransaction.objects.create(
                account=self.savings_account,
                transaction_type='DEPOSIT',
                amount=self.amount,
                balance_after=new_balance,
                date=self.sheet.date,
                description=f"Collection from sheet #{self.sheet.id}",
                created_by=self.sheet.collector
            )
            self.savings_account.current_balance = new_balance
            self.savings_account.save()
        # Fee collection – can be extended to accounting later

    def _reverse_effect(self, original):
        """Reverse the effect of the original entry (for edit or delete)"""
        if original.collection_type == 'loan' and original.loan_installment:
            # Reversing a loan payment is complex. For simplicity, we prevent editing loan entries.
            # Instead, we raise an error. A better approach is to create a reversal transaction.
            raise PermissionError("Editing or deleting a loan collection entry is not allowed. Please create a reversal entry instead.")
        elif original.collection_type == 'savings' and original.savings_account:
            from apps.savings.models import SavingsTransaction
            # Reverse the deposit (withdrawal)
            new_balance = self.savings_account.current_balance - original.amount
            SavingsTransaction.objects.create(
                account=self.savings_account,
                transaction_type='WITHDRAWAL',
                amount=original.amount,
                balance_after=new_balance,
                date=self.sheet.date,
                description=f"Reversal of collection entry #{original.id}",
                created_by=self.sheet.collector
            )
            self.savings_account.current_balance = new_balance
            self.savings_account.save()
        # Fee reversal – similar to above

    class Meta:
        permissions = [
            ('can_change_collectionentry', 'Can edit collection entries'),
            ('can_delete_collectionentry', 'Can delete collection entries'),
        ]