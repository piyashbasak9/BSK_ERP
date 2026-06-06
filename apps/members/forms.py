from django import forms
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from .models import Member, Nominee, MemberTransfer
import os


class MemberPhotoValidator:
    """Custom validator for member photos"""
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    
    def __call__(self, file):
        if not file:
            return
        
        # Check file size
        if file.size > self.MAX_SIZE:
            raise ValidationError(f'File size must not exceed {self.MAX_SIZE / 1024 / 1024}MB')
        
        # Check file extension
        ext = os.path.splitext(file.name)[1][1:].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(f'File type .{ext} is not allowed. Allowed types: {", ".join(self.ALLOWED_EXTENSIONS)}')


class MemberForm(forms.ModelForm):
    """Form for creating and editing members with validation"""
    
    class Meta:
        model = Member
        fields = [
            'branch', 'member_id', 'name', 'father_name', 'mother_name', 'spouse_name',
            'gender', 'marital_status', 'date_of_birth', 'nid', 'phone', 'email',
            'present_address', 'permanent_address', 'photo', 'is_active'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'present_address': forms.Textarea(attrs={'rows': 3}),
            'permanent_address': forms.Textarea(attrs={'rows': 3}),
        }
    
    photo = forms.ImageField(
        required=False,
        validators=[MemberPhotoValidator()],
        help_text='Max size: 5MB. Allowed formats: JPG, PNG, GIF, WebP'
    )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise ValidationError('Phone number is required')
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValidationError('Phone number must contain only digits and +, -, space')
        if len(phone.replace('+', '').replace('-', '').replace(' ', '')) < 10:
            raise ValidationError('Phone number must be at least 10 digits')
        return phone
    
    def clean_nid(self):
        nid = self.cleaned_data.get('nid', '').strip()
        if not nid:
            raise ValidationError('NID is required')
        if len(nid) < 10:
            raise ValidationError('NID must be at least 10 characters')
        return nid
    
    def clean_member_id(self):
        member_id = self.cleaned_data.get('member_id', '').strip()
        if not member_id:
            raise ValidationError('Member ID is required')
        return member_id
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            from django.utils import timezone
            today = timezone.now().date()
            age = (today - dob).days // 365
            if age < 18:
                raise ValidationError('Member must be at least 18 years old')
            if age > 120:
                raise ValidationError('Invalid date of birth')
        return dob
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email and '@' not in email:
            raise ValidationError('Invalid email address')
        return email


class NomineeForm(forms.ModelForm):
    """Form for member nominees"""
    
    class Meta:
        model = Nominee
        fields = ['name', 'relation', 'percentage', 'nid', 'phone']
    
    def clean_percentage(self):
        percentage = self.cleaned_data.get('percentage')
        if percentage and (percentage < 0 or percentage > 100):
            raise ValidationError('Percentage must be between 0 and 100')
        return percentage


class MemberTransferForm(forms.ModelForm):
    """Form for member branch transfer"""
    
    class Meta:
        model = MemberTransfer
        fields = ['from_branch', 'to_branch', 'transfer_date', 'reason']
        widgets = {
            'transfer_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        from_branch = cleaned_data.get('from_branch')
        to_branch = cleaned_data.get('to_branch')
        
        if from_branch and to_branch and from_branch == to_branch:
            raise ValidationError('Source and destination branches must be different')
        
        return cleaned_data
