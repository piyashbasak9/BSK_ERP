from django import forms
from .models import Branch


class BranchForm(forms.ModelForm):
    """Form for creating and editing branches"""
    
    class Meta:
        model = Branch
        fields = ['name', 'code', 'address', 'phone', 'email', 'opening_date', 'is_active']
        widgets = {
            'opening_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise forms.ValidationError('Branch code is required')
        if len(code) > 20:
            raise forms.ValidationError('Branch code must be 20 characters or less')
        return code
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Phone number is required')
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError('Phone number must contain only digits and +, -, space')
        return phone
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Branch name is required')
        return name
