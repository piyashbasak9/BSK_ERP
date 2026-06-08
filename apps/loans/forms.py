from django import forms
from django.core.exceptions import ValidationError
from .models import LoanProduct, LoanApplication, LoanDisbursement, LoanInstallmentSchedule
from datetime import date


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
        product = self.cleaned_data.get('product')
        
        if amount is None:
            return amount
        
        if amount <= 0:
            raise ValidationError('Applied amount must be greater than 0')
        
        # Validate against product limits
        if product:
            if amount < product.min_amount:
                raise ValidationError(f'Applied amount cannot be less than the product minimum amount ({product.min_amount}).')
            if amount > product.max_amount:
                raise ValidationError(f'Applied amount cannot exceed the product maximum amount ({product.max_amount}).')
        
        return amount
    
    def clean_applied_date(self):
        from django.utils import timezone
        date_val = self.cleaned_data.get('applied_date')
        if date_val and date_val > timezone.now().date():
            raise ValidationError('Application date cannot be in the future')
        return date_val

    def save(self, commit=True):
        application = super().save(commit=False)
        product = self.cleaned_data.get('product')
        if product:
            application.interest_rate_applied = product.interest_rate
        if commit:
            application.save()
        return application


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
        # Get the loan application instance (the object being edited)
        loan_app = self.instance
        
        if amount is None:
            return amount
        
        if amount <= 0:
            raise ValidationError('Approved amount must be greater than 0')
        
        # Validate against the product's limits
        if loan_app and loan_app.product:
            if amount < loan_app.product.min_amount:
                raise ValidationError(f'Approved amount cannot be less than the product minimum amount ({loan_app.product.min_amount}).')
            if amount > loan_app.product.max_amount:
                raise ValidationError(f'Approved amount cannot exceed the product maximum amount ({loan_app.product.max_amount}).')
        
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['loan'].queryset = LoanApplication.objects.filter(status='approved')
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        loan = self.cleaned_data.get('loan')
        
        if amount is None:
            return amount
        
        if amount <= 0:
            raise ValidationError('Disbursement amount must be greater than 0')
        
        # Ensure disbursement amount does not exceed the approved amount
        if loan and loan.approved_amount:
            if amount > loan.approved_amount:
                raise ValidationError(f'Disbursement amount cannot exceed the approved amount ({loan.approved_amount}).')
        
        return amount


class LoanDisbursementEditForm(forms.ModelForm):
    """
    Form for editing disbursement (only non-critical fields).
    Amount and loan cannot be changed to maintain data integrity.
    """
    class Meta:
        model = LoanDisbursement
        fields = ['disbursement_date', 'method', 'reference_no']
        widgets = {
            'disbursement_date': forms.DateInput(attrs={'type': 'date'}),
            'reference_no': forms.TextInput(attrs={'placeholder': 'Cheque no / Transaction ID'}),
        }

    def clean_disbursement_date(self):
        date_val = self.cleaned_data.get('disbursement_date')
        if date_val and date_val > date.today():
            raise ValidationError("Disbursement date cannot be in the future.")
        return date_val


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


class LoanPaymentForm(forms.Form):
    """
    Form to accept payment for a specific installment.
    Used in modal for collecting payments.
    """
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0.01,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        label="Payment Amount"
    )
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Payment Date", required=False,
        help_text="Leave blank for today's date"
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount