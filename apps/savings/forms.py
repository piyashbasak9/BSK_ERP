from django import forms
from django.core.exceptions import ValidationError
from .models import SavingsProduct, SavingsAccount, SavingsTransaction


class SavingsProductForm(forms.ModelForm):
    """Form for creating and editing savings products"""
    
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
    """Form for creating and editing savings accounts"""
    
    class Meta:
        model = SavingsAccount
        fields = ['member', 'product', 'opening_date', 'is_active']
        widgets = {
            'opening_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_opening_date(self):
        from django.utils import timezone
        opening_date = self.cleaned_data.get('opening_date')
        if opening_date and opening_date > timezone.now().date():
            raise ValidationError('Opening date cannot be in the future')
        return opening_date


class SavingsTransactionForm(forms.ModelForm):
    """Form for creating savings transactions"""
    
    class Meta:
        model = SavingsTransaction
        fields = ['account', 'transaction_type', 'amount', 'date', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Amount must be greater than 0')
        return amount
    
    def clean_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError('Transaction date cannot be in the future')
        return date
