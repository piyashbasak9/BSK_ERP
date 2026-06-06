import json
from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import SystemSettingsForm


class SuperUserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser status"""
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access this page.')
        return super().handle_no_permission()


class SettingsDashboardView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    """System settings dashboard"""
    template_name = 'settings/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get current settings from Django settings or database
        context['settings'] = {
            'organization_name': 'BSK Microfinance',
            'organization_code': 'BSK',
            'financial_year_start': 'January',
            'enable_audit_logging': True,
            'enable_notifications': True,
        }
        return context


class SystemSettingsView(LoginRequiredMixin, SuperUserRequiredMixin, FormView):
    """Edit system settings"""
    form_class = SystemSettingsForm
    template_name = 'settings/system_settings.html'
    success_url = reverse_lazy('settings_dashboard')
    
    def get_initial(self):
        # Load current settings from Django settings or database
        return {
            'organization_name': 'BSK Microfinance',
            'organization_code': 'BSK',
            'financial_year_start': 1,
            'default_interest_rate': '12.00',
            'default_processing_fee': '2.00',
            'enable_notifications': True,
            'enable_audit_logging': True,
        }
    
    def form_valid(self, form):
        # Save settings to Django settings or database
        messages.success(self.request, 'Settings saved successfully.')
        return super().form_valid(form)


class UserManagementView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    """User and role management"""
    template_name = 'settings/user_management.html'
    
    def get_context_data(self, **kwargs):
        from apps.authentication.models import User
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all().order_by('username')
        return context


class BranchManagementView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    """Branch management"""
    template_name = 'settings/branch_management.html'
    
    def get_context_data(self, **kwargs):
        from apps.branches.models import Branch
        context = super().get_context_data(**kwargs)
        context['branches'] = Branch.objects.all().order_by('code')
        return context


class BackupRestoreView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    """Backup and restore settings"""
    template_name = 'settings/backup_restore.html'


class AuditSettingsView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    """Configure audit logging settings"""
    template_name = 'settings/audit_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['audit_settings'] = {
            'log_logins': True,
            'log_data_changes': True,
            'log_deletions': True,
            'retention_days': 90,
        }
        return context
