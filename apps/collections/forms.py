from django import forms
from django.core.exceptions import ValidationError
from .models import DailyCollectionSheet, CollectionEntry


class DailyCollectionSheetForm(forms.ModelForm):
    """Form for creating daily collection sheets"""
    
    class Meta:
        model = DailyCollectionSheet
        fields = ['date', 'branch', 'verified']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError('Collection date cannot be in the future')
        return date


class CollectionEntryForm(forms.ModelForm):
    """Form for creating collection entries"""
    
    class Meta:
        model = CollectionEntry
        fields = [
            'sheet', 'member', 'collection_type', 'loan_installment',
            'savings_account', 'amount', 'principal', 'interest', 'late_fee', 'remark'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'principal': forms.NumberInput(attrs={'step': '0.01'}),
            'interest': forms.NumberInput(attrs={'step': '0.01'}),
            'late_fee': forms.NumberInput(attrs={'step': '0.01'}),
            'remark': forms.Textarea(attrs={'rows': 3}),
        }
    
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
        
        if collection_type == 'loan' and not loan_installment:
            raise ValidationError('Loan installment is required for loan collection')
        if collection_type == 'savings' and not savings_account:
            raise ValidationError('Savings account is required for savings collection')
        
        return cleaned_data
