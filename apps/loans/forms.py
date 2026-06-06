from django import forms
from django.core.exceptions import ValidationError
from .models import LoanProduct, LoanApplication, LoanDisbursement, LoanInstallmentSchedule


class LoanProductForm(forms.ModelForm):
    """Form for creating and editing loan products"""
    
    class Meta:
        model = LoanProduct
        fields = [
            'name', 'code', 'interest_rate', 'max_amount', 'min_amount',
            'duration_months', 'installment_frequency', 'processing_fee', 'late_penalty_rate', 'is_active'
        ]
        widgets = {
            'interest_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'min_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'processing_fee': forms.NumberInput(attrs={'step': '0.01'}),
            'late_penalty_rate': forms.NumberInput(attrs={'step': '0.01'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError('Product code is required')
        return code
    
    def clean_min_amount(self):
        amount = self.cleaned_data.get('min_amount')
        if amount is not None and amount < 0:
            raise ValidationError('Minimum amount cannot be negative')
        return amount
    
    def clean_max_amount(self):
        max_amount = self.cleaned_data.get('max_amount')
        min_amount = self.cleaned_data.get('min_amount')
        if max_amount is not None and max_amount < 0:
            raise ValidationError('Maximum amount cannot be negative')
        if max_amount and min_amount and max_amount < min_amount:
            raise ValidationError('Maximum amount must be greater than minimum amount')
        return max_amount


class LoanApplicationForm(forms.ModelForm):
    """Form for creating loan applications"""
    
    class Meta:
        model = LoanApplication
        fields = ['member', 'product', 'applied_amount', 'duration', 'purpose', 'applied_date']
        widgets = {
            'applied_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'applied_date': forms.DateInput(attrs={'type': 'date'}),
            'purpose': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_applied_amount(self):
        amount = self.cleaned_data.get('applied_amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Applied amount must be greater than 0')
        return amount
    
    def clean_applied_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('applied_date')
        if date and date > timezone.now().date():
            raise ValidationError('Application date cannot be in the future')
        return date


class LoanApplicationApprovalForm(forms.ModelForm):
    """Form for approving loan applications"""
    
    class Meta:
        model = LoanApplication
        fields = ['approved_amount', 'status', 'approved_date']
        widgets = {
            'approved_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'approved_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_approved_amount(self):
        amount = self.cleaned_data.get('approved_amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Approved amount must be greater than 0')
        return amount


class LoanDisbursementForm(forms.ModelForm):
    """Form for recording loan disbursements"""
    
    class Meta:
        model = LoanDisbursement
        fields = ['loan', 'amount', 'disbursement_date', 'method', 'reference_no']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'disbursement_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Disbursement amount must be greater than 0')
        return amount


class LoanInstallmentScheduleForm(forms.ModelForm):
    """Form for loan installment schedules"""
    
    class Meta:
        model = LoanInstallmentSchedule
        fields = [
            'loan', 'installment_no', 'due_date', 'principal_amount',
            'interest_amount', 'paid_principal', 'paid_interest', 'paid_date', 'is_paid'
        ]
        widgets = {
            'principal_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'interest_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'paid_principal': forms.NumberInput(attrs={'step': '0.01'}),
            'paid_interest': forms.NumberInput(attrs={'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
        }
