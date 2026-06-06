import json
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q
from apps.members.models import Member
from apps.loans.models import LoanApplication, LoanInstallmentSchedule
from apps.savings.models import SavingsAccount, SavingsProduct, SavingsTransaction
from apps.collections.models import DailyCollectionSheet, CollectionEntry
from apps.accounting.models import Account, JournalEntry
from apps.branches.models import Branch
from .forms import ReportFilterForm


class ReportListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """List available reports"""
    permission_required = 'reports.view_report'
    template_name = 'reports/report_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = [
            {
                'name': 'Member Summary',
                'description': 'Overview of all members',
                'url': 'report_member_summary'
            },
            {
                'name': 'Loan Summary',
                'description': 'Loan applications and status',
                'url': 'report_loan_summary'
            },
            {
                'name': 'Savings Summary',
                'description': 'Savings accounts and balances',
                'url': 'report_savings_summary'
            },
            {
                'name': 'Collection Summary',
                'description': 'Daily collections overview',
                'url': 'report_collection_summary'
            },
            {
                'name': 'Account Balance',
                'description': 'Trial balance and account status',
                'url': 'report_account_balance'
            },
        ]
        return context


class ReportDataMixin:
    """Mixin for common report functionality"""
    
    def get_date_range(self, date_range, start_date=None, end_date=None):
        """Get date range based on selection"""
        today = timezone.now().date()
        
        if date_range == 'today':
            return today, today
        elif date_range == 'this_week':
            start = today - timedelta(days=today.weekday())
            return start, today
        elif date_range == 'this_month':
            return today.replace(day=1), today
        elif date_range == 'this_year':
            return today.replace(month=1, day=1), today
        elif date_range == 'custom':
            return start_date or today, end_date or today
        return today, today


class MemberSummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Member summary report"""
    permission_required = 'reports.view_report'
    template_name = 'reports/member_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = Member.objects.filter(is_deleted=False)
        if not self.request.user.is_superuser and self.request.user.branch:
            queryset = queryset.filter(branch=self.request.user.branch)
        
        context['total_members'] = queryset.count()
        context['active_members'] = queryset.filter(is_active=True).count()
        context['inactive_members'] = queryset.filter(is_active=False).count()
        
        # By branch
        context['members_by_branch'] = queryset.values('branch__name').annotate(count=Count('id')).order_by('-count')
        
        return context


class LoanSummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Loan summary report"""
    permission_required = 'reports.view_report'
    template_name = 'reports/loan_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = LoanApplication.objects.all()
        if not self.request.user.is_superuser and self.request.user.branch:
            queryset = queryset.filter(member__branch=self.request.user.branch)
        
        context['total_loans'] = queryset.count()
        context['pending_loans'] = queryset.filter(status='pending').count()
        context['approved_loans'] = queryset.filter(status='approved').count()
        context['disbursed_loans'] = queryset.filter(status='disbursed').count()
        context['closed_loans'] = queryset.filter(status='closed').count()
        
        # Total amounts
        context['total_applied_amount'] = queryset.aggregate(Sum('applied_amount'))['applied_amount__sum'] or 0
        context['total_approved_amount'] = queryset.filter(approved_amount__isnull=False).aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0
        
        # By status
        context['loans_by_status'] = queryset.values('status').annotate(count=Count('id')).order_by('-count')
        
        return context


class SavingsSummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Savings summary report"""
    permission_required = 'reports.view_report'
    template_name = 'reports/savings_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = SavingsAccount.objects.filter(is_deleted=False)
        if not self.request.user.is_superuser and self.request.user.branch:
            queryset = queryset.filter(member__branch=self.request.user.branch)
        
        context['total_accounts'] = queryset.count()
        context['active_accounts'] = queryset.filter(is_active=True).count()
        context['inactive_accounts'] = queryset.filter(is_active=False).count()
        
        # Total balance
        context['total_balance'] = queryset.aggregate(Sum('current_balance'))['current_balance__sum'] or 0
        
        # By product
        context['accounts_by_product'] = queryset.values('product__name').annotate(
            count=Count('id'),
            total_balance=Sum('current_balance')
        ).order_by('-count')
        
        return context


class CollectionSummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Collection summary report"""
    permission_required = 'reports.view_report'
    template_name = 'reports/collection_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        date_range = self.request.GET.get('date_range', 'this_month')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        today = timezone.now().date()
        if date_range == 'this_month':
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
        
        queryset = DailyCollectionSheet.objects.filter(date__range=[start_date, end_date])
        if not self.request.user.is_superuser and self.request.user.branch:
            queryset = queryset.filter(branch=self.request.user.branch)
        
        context['total_sheets'] = queryset.count()
        context['total_cash'] = queryset.aggregate(Sum('total_cash'))['total_cash__sum'] or 0
        context['verified_sheets'] = queryset.filter(verified=True).count()
        
        # By collection type
        entries = CollectionEntry.objects.filter(sheet__date__range=[start_date, end_date])
        if not self.request.user.is_superuser and self.request.user.branch:
            entries = entries.filter(sheet__branch=self.request.user.branch)
        
        context['collections_by_type'] = entries.values('collection_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-count')
        
        return context


class AccountBalanceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Account balance (trial balance) report"""
    permission_required = 'reports.view_report'
    template_name = 'reports/account_balance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = Account.objects.filter(is_active=True)
        if not self.request.user.is_superuser and self.request.user.branch:
            queryset = queryset.filter(Q(branch=self.request.user.branch) | Q(branch__isnull=True))
        
        accounts = []
        total_debit = 0
        total_credit = 0
        
        for account in queryset.order_by('account_type', 'code'):
            items = account.journalitem_set.all()
            debit = items.aggregate(Sum('debit'))['debit__sum'] or 0
            credit = items.aggregate(Sum('credit'))['credit__sum'] or 0
            
            accounts.append({
                'code': account.code,
                'name': account.name,
                'type': account.account_type,
                'debit': debit,
                'credit': credit,
            })
            
            total_debit += debit
            total_credit += credit
        
        context['accounts'] = accounts
        context['total_debit'] = total_debit
        context['total_credit'] = total_credit
        
        return context


class ReportExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export report as CSV"""
    permission_required = 'reports.view_report'
    
    def get(self, request, report_type):
        # Implement CSV export functionality
        return JsonResponse({'error': 'Not implemented'}, status=501)
