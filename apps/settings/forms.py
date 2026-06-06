from django import forms


class SystemSettingsForm(forms.Form):
    """Form for system settings"""
    
    FINANCIAL_YEAR_START = [
        (1, 'January'),
        (4, 'April'),
        (7, 'July'),
        (10, 'October'),
    ]
    
    organization_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    organization_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    organization_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    financial_year_start = forms.ChoiceField(
        choices=FINANCIAL_YEAR_START,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    default_interest_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    default_processing_fee = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    enable_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    enable_audit_logging = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
