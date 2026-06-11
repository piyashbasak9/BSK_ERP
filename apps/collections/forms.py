from django import forms
from django.core.exceptions import ValidationError
from .models import DailyCollectionSheet, CollectionEntry
from apps.loans.models import LoanInstallmentSchedule
from apps.savings.models import SavingsAccount


class DailyCollectionSheetForm(forms.ModelForm):
    class Meta:
        model = DailyCollectionSheet
        fields = ['date', 'branch']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_date(self):
        from django.utils import timezone
        date_val = self.cleaned_data.get('date')
        if date_val and date_val > timezone.now().date():
            raise ValidationError('Collection date cannot be in the future')
        return date_val


class CollectionEntryForm(forms.ModelForm):
    class Meta:
        model = CollectionEntry
        fields = [
            'sheet', 'member', 'collection_type', 'loan_installment',
            'savings_account', 'amount', 'remark'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'remark': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit sheets to unverified ones only (if creating new entry)
        if not self.instance.pk:
            self.fields['sheet'].queryset = DailyCollectionSheet.objects.filter(verified=False)
        # Limit loan installments to unpaid ones for the selected member (will be refined in clean)
        # Limit savings accounts to active ones for the selected member

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Collection amount must be greater than 0')
        return amount

    def clean(self):
        cleaned_data = super().clean()
        collection_type = cleaned_data.get('collection_type')
        loan_installment = cleaned_data.get('loan_installment')
        savings_account = cleaned_data.get('savings_account')
        amount = cleaned_data.get('amount')
        member = cleaned_data.get('member')

        if collection_type == 'loan':
            if not loan_installment:
                raise ValidationError('Loan installment is required for loan collection')
            # Verify the installment belongs to the selected member and is not fully paid
            if member and loan_installment.loan.member != member:
                raise ValidationError('Selected installment does not belong to this member')
            remaining_due = loan_installment.total_due - loan_installment.paid_total
            if remaining_due <= 0:
                raise ValidationError('This installment is already fully paid')
            if amount and amount > remaining_due:
                raise ValidationError(f'Amount cannot exceed remaining due of {remaining_due}')

        elif collection_type == 'savings':
            if not savings_account:
                raise ValidationError('Savings account is required for savings deposit')
            if member and savings_account.member != member:
                raise ValidationError('Selected savings account does not belong to this member')
            if not savings_account.is_active or savings_account.is_deleted:
                raise ValidationError('This savings account is not active')
        else:  # fee
            pass  # No extra validation

        return cleaned_data