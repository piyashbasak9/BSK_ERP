from django import forms
from .models import AuditLog

class AuditLogFilterForm(forms.Form):
    LOG_TYPES = [(choice[0], choice[1]) for choice in AuditLog.ACTION_CHOICES]
    log_type = forms.MultipleChoiceField(
        choices=LOG_TYPES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    user = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )