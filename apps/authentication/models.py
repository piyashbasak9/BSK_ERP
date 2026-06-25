from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.branches.models import Branch


class AllowedUrl(models.Model):
    name = models.CharField(max_length=200, unique=True)
    url_name = models.CharField(max_length=200, unique=True)
    path = models.CharField(max_length=300, blank=True, help_text='Optional display path for the URL')
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Allowed URL'
        verbose_name_plural = 'Allowed URLs'

    def __str__(self):
        return self.name


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
    allowed_urls = models.ManyToManyField('AllowedUrl', blank=True, related_name='users')

    class Meta:
        permissions = [
            ('can_view_all_branches', 'Can view all branches'),
            ('can_manage_system_settings', 'Can manage system settings'),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_allowed_url_names(self):
        if hasattr(self, '_allowed_url_names_cache') and self._allowed_url_names_cache is not None:
            return self._allowed_url_names_cache
        names = set(self.allowed_urls.values_list('url_name', flat=True))
        try:
            # cache on instance for the duration of the request
            self._allowed_url_names_cache = names
        except Exception:
            pass
        return names

    def can_access_url(self, url_name):
        if self.is_superuser:
            return True
        return url_name in self.get_allowed_url_names()
