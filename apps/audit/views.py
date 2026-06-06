import json
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from .forms import AuditLogFilterForm
from erp.utils.tabulator import TabulatorGrid


class SuperUserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser status"""
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        from django.contrib import messages
        messages.error(self.request, 'You do not have permission to view audit logs.')
        return super().handle_no_permission()


class AuditLogListView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    """List audit logs with filtering"""
    template_name = 'audit/log_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Timestamp", "field": "timestamp", "width": 150},
            {"title": "User", "field": "user", "sorter": "string", "width": 120},
            {"title": "Action", "field": "action", "width": 100},
            {"title": "Resource", "field": "resource", "sorter": "string", "widthGrow": 1},
            {"title": "IP Address", "field": "ip_address", "width": 120},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        
        # Get audit logs (placeholder - would come from middleware/logging system)
        logs = self.get_audit_logs()
        
        paginator = Paginator(logs, 20)
        page_obj = paginator.get_page(1)
        
        initial_list = [
            {
                'id': i,
                'timestamp': log.get('timestamp', ''),
                'user': log.get('user', ''),
                'action': log.get('action', ''),
                'resource': log.get('resource', ''),
                'ip_address': log.get('ip_address', ''),
            }
            for i, log in enumerate(page_obj.object_list)
        ]
        
        context['initial_logs'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        
        context['filter_form'] = AuditLogFilterForm(self.request.GET)
        return context
    
    def get_audit_logs(self):
        """Get audit logs from the system"""
        # This would normally query a database or log file
        # For now, return empty list as placeholder
        return []


class AuditLogGridDataView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    """AJAX endpoint for audit log data"""
    
    def get(self, request):
        # Get audit logs with filtering
        logs = self.get_filtered_logs(request)
        
        # Apply pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(logs, 20)
        page_obj = paginator.get_page(page)
        
        data = [
            {
                'id': i,
                'timestamp': log.get('timestamp', ''),
                'user': log.get('user', ''),
                'action': log.get('action', ''),
                'resource': log.get('resource', ''),
                'ip_address': log.get('ip_address', ''),
            }
            for i, log in enumerate(page_obj.object_list)
        ]
        
        return JsonResponse({
            'last_page': paginator.num_pages,
            'data': data,
            'current_page': int(page),
        })
    
    def get_filtered_logs(self, request):
        """Get and filter audit logs"""
        # This would normally query a database
        return []


class AuditLogDetailView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    """View detailed audit log entry"""
    
    def get(self, request, log_id):
        # Get specific log entry
        log_entry = {
            'id': log_id,
            'timestamp': timezone.now().isoformat(),
            'user': 'admin',
            'action': 'update',
            'resource': 'Member',
            'resource_id': 1,
            'old_values': {'name': 'Old Name'},
            'new_values': {'name': 'New Name'},
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0...',
        }
        
        return JsonResponse(log_entry)


class AuditLogExportView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    """Export audit logs"""
    
    def get(self, request):
        # Export logs in CSV or Excel format
        return JsonResponse({'error': 'Not implemented'}, status=501)


class SystemActivityDashboardView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    """System activity dashboard"""
    template_name = 'audit/activity_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        context['today_logins'] = 15  # Placeholder
        context['today_data_changes'] = 42  # Placeholder
        context['today_deletions'] = 2  # Placeholder
        context['active_sessions'] = 8  # Placeholder
        
        # Recent activities
        context['recent_activities'] = [
            {
                'timestamp': timezone.now().isoformat(),
                'user': 'admin',
                'action': 'Created member',
                'resource': 'Member #123',
            },
            {
                'timestamp': timezone.now().isoformat(),
                'user': 'user1',
                'action': 'Updated loan',
                'resource': 'Loan #456',
            },
        ]
        
        return context
