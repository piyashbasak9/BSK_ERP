from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.branches.models import Branch

class User(AbstractUser):
    ROLE_CHOICES = (
        ('branch_manager', 'Branch Manager'),
        ('accountant', 'Accountant'),
        ('field_officer', 'Field Officer'),
        ('auditor', 'Auditor'),
    )
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='field_officer')
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        permissions = [
            ('can_view_all_branches', 'Can view all branches'),
            ('can_manage_system_settings', 'Can manage system settings'),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"