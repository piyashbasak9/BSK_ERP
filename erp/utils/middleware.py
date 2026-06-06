import threading
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import resolve
import json

_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_ip():
    return getattr(_thread_locals, 'ip', None)

class BranchIsolationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            _thread_locals.branch = request.user.branch
        else:
            _thread_locals.branch = None

class RBACMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None
        if request.user.is_superuser:
            return None
        resolver = resolve(request.path_info)
        url_name = resolver.url_name
        # Map URL names to required permissions (simplified example)
        perm_map = {
            'member_list': 'members.view_member',
            'member_add': 'members.add_member',
            'member_edit': 'members.change_member',
            'member_delete': 'members.delete_member',
            'savings_account_list': 'savings.view_savingsaccount',
            'savings_deposit': 'savings.add_savingstransaction',
            'savings_withdraw': 'savings.add_savingstransaction',
            'loans_application_list': 'loans.view_loanapplication',
            'loan_approve': 'loans.change_loanapplication',
            'loan_disburse': 'loans.disburse_loan',
            'collection_entry': 'collections.add_collection',
            'collection_verify': 'collections.verify_collection',
            'reports_view': 'reports.view_report',
            'audit_log_view': 'audit.view_auditlog',
        }
        if url_name in perm_map:
            if not request.user.has_perm(perm_map[url_name]):
                return redirect('dashboard')
        return None

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_locals.user = request.user if request.user.is_authenticated else None
        _thread_locals.ip = self.get_client_ip(request)
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')