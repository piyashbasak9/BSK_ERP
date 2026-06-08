from django import forms
from django.core.exceptions import ValidationError
from .models import SavingsProduct, SavingsAccount, SavingsTransaction
from apps.members.models import Member


class SavingsProductForm(forms.ModelForm):
    class Meta:
        model = SavingsProduct
        fields = ['name', 'code', 'interest_rate', 'min_balance', 'service_charge', 'is_active']
        widgets = {
            'interest_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'min_balance': forms.NumberInput(attrs={'step': '0.01'}),
            'service_charge': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError('Product code is required')
        if len(code) > 20:
            raise ValidationError('Product code must be 20 characters or less')
        return code

    def clean_interest_rate(self):
        rate = self.cleaned_data.get('interest_rate')
        if rate is not None and rate < 0:
            raise ValidationError('Interest rate cannot be negative')
        return rate

    def clean_min_balance(self):
        balance = self.cleaned_data.get('min_balance')
        if balance is not None and balance < 0:
            raise ValidationError('Minimum balance cannot be negative')
        return balance


class SavingsAccountForm(forms.ModelForm):
    opening_balance = forms.DecimalField(
        max_digits=15, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={'step': '0.01'}),
        label="Initial Deposit",
        help_text="Must be at least the product's minimum balance"
    )

    class Meta:
        model = SavingsAccount
        fields = ['member', 'product', 'opening_date', 'opening_balance']
        widgets = {
            'opening_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Filter members by branch if user is not superuser
        if self.request and not self.request.user.is_superuser and self.request.user.branch:
            self.fields['member'].queryset = Member.objects.filter(branch=self.request.user.branch, is_deleted=False)
        # Initially no product selected, so we dynamically filter later in clean

    def clean_opening_date(self):
        from django.utils import timezone
        opening_date = self.cleaned_data.get('opening_date')
        if opening_date and opening_date > timezone.now().date():
            raise ValidationError('Opening date cannot be in the future')
        return opening_date

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        opening_balance = cleaned_data.get('opening_balance')
        if product and opening_balance:
            if opening_balance < product.min_balance:
                raise ValidationError(f'Initial deposit must be at least {product.min_balance} (minimum balance for this product).')
        return cleaned_data


class SavingsTransactionForm(forms.ModelForm):
    class Meta:
        model = SavingsTransaction
        fields = ['account', 'transaction_type', 'amount', 'date', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Only show active, non-deleted accounts; filter by branch if needed
        queryset = SavingsAccount.objects.filter(is_active=True, is_deleted=False)
        if self.request and not self.request.user.is_superuser and self.request.user.branch:
            queryset = queryset.filter(member__branch=self.request.user.branch)
        self.fields['account'].queryset = queryset

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Amount must be greater than 0')
        return amount

    def clean_date(self):
        from django.utils import timezone
        date_val = self.cleaned_data.get('date')
        if date_val and date_val > timezone.now().date():
            raise ValidationError('Transaction date cannot be in the future')
        return date_val

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        transaction_type = cleaned_data.get('transaction_type')
        amount = cleaned_data.get('amount')

        if account and transaction_type and amount:
            if transaction_type == 'WITHDRAWAL':
                if amount > account.current_balance:
                    raise ValidationError(f'Insufficient balance. Available: {account.current_balance}')
                # Check minimum balance after withdrawal
                if (account.current_balance - amount) < account.product.min_balance:
                    raise ValidationError(f'Withdrawal would violate minimum balance requirement of {account.product.min_balance}')
        return cleaned_data