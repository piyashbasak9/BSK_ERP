from django import forms


class AuditLogFilterForm(forms.Form):
    """Form for filtering audit logs"""
    
    LOG_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
    ]
    
    log_type = forms.MultipleChoiceField(
        choices=LOG_TYPES,
        required=False,
        widget=forms.CheckboxSelectMultiple()
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
