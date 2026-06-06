from django import forms


class ReportFilterForm(forms.Form):
    """Form for filtering reports"""
    
    START_DATE_CHOICES = [
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
        choices=START_DATE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    branch = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )
