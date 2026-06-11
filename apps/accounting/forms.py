from django import forms
from django.core.exceptions import ValidationError
from .models import Account, JournalEntry, JournalItem

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type', 'parent', 'is_active', 'branch']

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError('Account code is required')
        if len(code) > 20:
            raise ValidationError('Account code must be 20 characters or less')
        return code

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('Account name is required')
        return name


class JournalEntryForm(forms.ModelForm):
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
            raise ValidationError('Voucher number is required')
        return voucher_no


class JournalItemForm(forms.ModelForm):
    class Meta:
        model = JournalItem
        fields = ['account', 'debit', 'credit', 'reference_no']
        widgets = {
            'debit': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control debit-input'}),
            'credit': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control credit-input'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit') or 0
        credit = cleaned_data.get('credit') or 0

        if debit < 0 or credit < 0:
            raise ValidationError('Debit and credit amounts must be positive')

        if debit > 0 and credit > 0:
            raise ValidationError('Both debit and credit cannot have values in same line')

        if debit == 0 and credit == 0:
            raise ValidationError('Either debit or credit must have a value')

        return cleaned_data


# Inline formset for Journal Items
from django.forms import inlineformset_factory

JournalItemFormSet = inlineformset_factory(
    JournalEntry,
    JournalItem,
    form=JournalItemForm,
    extra=2,
    can_delete=True,
    min_num=2,
    validate_min=True,
    validate_max=False
)