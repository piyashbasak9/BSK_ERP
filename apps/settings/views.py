import json
from django.views.generic import TemplateView, FormView, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse
from django.core.management import call_command
from io import StringIO
from .forms import SystemSettingsForm
from .models import SystemSetting
from apps.authentication.models import User
from apps.branches.models import Branch


class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access this page.')
        return redirect('settings_dashboard')


class SettingsDashboardView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'settings/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = {
            'organization_name': SystemSetting.get('organization_name', 'BSK Microfinance'),
            'organization_code': SystemSetting.get('organization_code', 'BSK'),
            'financial_year_start': SystemSetting.get('financial_year_start', 1),
            'enable_audit_logging': SystemSetting.get('enable_audit_logging', True),
            'enable_notifications': SystemSetting.get('enable_notifications', True),
        }
        return context


class SystemSettingsView(LoginRequiredMixin, SuperUserRequiredMixin, FormView):
    form_class = SystemSettingsForm
    template_name = 'settings/system_settings.html'
    success_url = reverse_lazy('settings_dashboard')

    def get_initial(self):
        return {
            'organization_name': SystemSetting.get('organization_name', 'BSK Microfinance'),
            'organization_code': SystemSetting.get('organization_code', 'BSK'),
            'organization_address': SystemSetting.get('organization_address', ''),
            'financial_year_start': SystemSetting.get('financial_year_start', 1),
            'default_interest_rate': SystemSetting.get('default_interest_rate', 12.00),
            'default_processing_fee': SystemSetting.get('default_processing_fee', 2.00),
            'enable_notifications': SystemSetting.get('enable_notifications', True),
            'enable_audit_logging': SystemSetting.get('enable_audit_logging', True),
        }

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'System settings saved successfully.')
        return super().form_valid(form)


# ============ USER MANAGEMENT ============
class UserListView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'settings/user_management.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all().order_by('username')
        return context

class UserCreateView(LoginRequiredMixin, SuperUserRequiredMixin, CreateView):
    model = User
    fields = ['username', 'password', 'first_name', 'last_name', 'email', 'branch', 'is_active', 'is_superuser', 'is_staff']
    template_name = 'settings/user_form.html'
    success_url = reverse_lazy('user_management')
    def form_valid(self, form):
        form.instance.set_password(form.cleaned_data['password'])
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, SuperUserRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email', 'branch', 'is_active', 'is_superuser', 'is_staff']
    template_name = 'settings/user_form.html'
    success_url = reverse_lazy('user_management')

class UserDeleteView(LoginRequiredMixin, SuperUserRequiredMixin, DeleteView):
    model = User
    template_name = 'settings/confirm_delete.html'
    success_url = reverse_lazy('user_management')


# ============ BRANCH MANAGEMENT ============
class BranchListView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'settings/branch_management.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branches'] = Branch.objects.all().order_by('code')
        return context

class BranchCreateView(LoginRequiredMixin, SuperUserRequiredMixin, CreateView):
    model = Branch
    fields = ['code', 'name', 'address', 'phone', 'email', 'is_active']
    template_name = 'settings/branch_form.html'
    success_url = reverse_lazy('branch_management')

class BranchUpdateView(LoginRequiredMixin, SuperUserRequiredMixin, UpdateView):
    model = Branch
    fields = ['code', 'name', 'address', 'phone', 'email', 'is_active']
    template_name = 'settings/branch_form.html'
    success_url = reverse_lazy('branch_management')

class BranchDeleteView(LoginRequiredMixin, SuperUserRequiredMixin, DeleteView):
    model = Branch
    template_name = 'settings/confirm_delete.html'
    success_url = reverse_lazy('branch_management')


# ============ BACKUP & RESTORE ============
class BackupRestoreView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'settings/backup_restore.html'

    def post(self, request):
        action = request.POST.get('action')
        if action == 'backup':
            out = StringIO()
            call_command('dumpdata', stdout=out, exclude=['contenttypes', 'auth.permission', 'sessions'])
            response = HttpResponse(out.getvalue(), content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="erp_backup.json"'
            return response
        elif action == 'restore':
            if 'backup_file' in request.FILES:
                file_content = request.FILES['backup_file'].read().decode('utf-8')
                # This would require clearing DB first – for safety we just show a message
                messages.warning(request, 'Restore is disabled for security. Use management command manually.')
            return redirect('backup_restore')
        return redirect('backup_restore')


# ============ AUDIT SETTINGS ============
class AuditSettingsView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'settings/audit_settings.html'

    def post(self, request):
        from apps.audit.models import AuditLog
        retention_days = int(request.POST.get('retention_days', 90))
        log_logins = request.POST.get('log_logins') == 'on'
        log_data_changes = request.POST.get('log_data_changes') == 'on'
        log_deletions = request.POST.get('log_deletions') == 'on'
        # Save to SystemSetting
        SystemSetting.set('audit_retention_days', retention_days, 'int')
        SystemSetting.set('audit_log_logins', log_logins, 'bool')
        SystemSetting.set('audit_log_data_changes', log_data_changes, 'bool')
        SystemSetting.set('audit_log_deletions', log_deletions, 'bool')
        messages.success(request, 'Audit settings saved.')
        return redirect('audit_settings')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['audit_settings'] = {
            'log_logins': SystemSetting.get('audit_log_logins', True),
            'log_data_changes': SystemSetting.get('audit_log_data_changes', True),
            'log_deletions': SystemSetting.get('audit_log_deletions', True),
            'retention_days': SystemSetting.get('audit_retention_days', 90),
        }
        return context