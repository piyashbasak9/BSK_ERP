from django import forms
from .models import Account, JournalEntry, JournalItem


class AccountForm(forms.ModelForm):
    """Form for creating and editing accounts"""
    
    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type', 'parent', 'is_active', 'branch']
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise forms.ValidationError('Account code is required')
        if len(code) > 20:
            raise forms.ValidationError('Account code must be 20 characters or less')
        return code
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Account name is required')
        return name


class JournalEntryForm(forms.ModelForm):
    """Form for creating journal entries"""
    
    class Meta:
        model = JournalEntry
        fields = ['voucher_no', 'date', 'description', 'branch']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_voucher_no(self):
        voucher_no = self.cleaned_data.get('voucher_no', '').strip()
        if not voucher_no:
            raise forms.ValidationError('Voucher number is required')
        return voucher_no


class JournalItemForm(forms.ModelForm):
    """Form for journal line items"""
    
    class Meta:
        model = JournalItem
        fields = ['account', 'debit', 'credit', 'reference_no']
    
    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit') or 0
        credit = cleaned_data.get('credit') or 0
        
        if debit < 0 or credit < 0:
            raise forms.ValidationError('Debit and credit amounts must be positive')
        
        if debit > 0 and credit > 0:
            raise forms.ValidationError('Both debit and credit cannot have values in same line')
        
        if debit == 0 and credit == 0:
            raise forms.ValidationError('Either debit or credit must have a value')
        
        return cleaned_data
