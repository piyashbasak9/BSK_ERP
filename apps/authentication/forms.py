from django import forms
from apps.authentication.models import User, AllowedUrl


class UserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Required for new users. Leave blank to keep the current password when editing existing users.'
    )
    allowed_urls = forms.ModelMultipleChoiceField(
        queryset=AllowedUrl.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Allowed URLs',
        help_text='Select which application URLs this user is allowed to access.'
    )

    class Meta:
        model = User
        fields = [
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'branch',
            'is_active',
            'is_superuser',
            'is_staff',
            'allowed_urls',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['allowed_urls'].queryset = AllowedUrl.objects.order_by('name')
        except Exception:
            self.fields['allowed_urls'].queryset = AllowedUrl.objects.none()

        standard_fields = ['username', 'first_name', 'last_name', 'email', 'branch', 'password']
        for name in standard_fields:
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-control'})
        boolean_fields = ['is_active', 'is_superuser', 'is_staff']
        for name in boolean_fields:
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        if self.instance.pk is None and not password:
            self.add_error('password', 'Password is required for new users.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user
