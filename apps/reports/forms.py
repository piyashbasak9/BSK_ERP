from django import forms
from apps.branches.models import Branch


class ReportFilterForm(forms.Form):
    """Form for filtering reports"""
    
    DATE_RANGE_CHOICES = [
        ('today', 'Today'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
        ('this_year', 'This Year'),
        ('custom', 'Custom Range'),
    ]
    
    report_type = forms.ChoiceField(
        choices=[
            ('member_summary', 'Member Summary'),
            ('loan_summary', 'Loan Summary'),
            ('savings_summary', 'Savings Summary'),
            ('collection_summary', 'Collection Summary'),
            ('account_balance', 'Account Balance'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        empty_label="All Branches",
        widget=forms.Select(attrs={'class': 'form-select'})
    )