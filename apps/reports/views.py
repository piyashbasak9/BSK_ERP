import csv
from datetime import datetime, timedelta
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from apps.members.models import Member
from apps.loans.models import LoanApplication
from apps.savings.models import SavingsAccount
from apps.collections.models import DailyCollectionSheet, CollectionEntry
from apps.accounting.models import Account
from apps.branches.models import Branch
from .forms import ReportFilterForm


class ReportListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'reports.view_report'
    template_name = 'reports/report_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = [
            {'name': 'Member Summary', 'description': 'Overview of all members', 'url': 'report_member_summary'},
            {'name': 'Loan Summary', 'description': 'Loan applications and status', 'url': 'report_loan_summary'},
            {'name': 'Savings Summary', 'description': 'Savings accounts and balances', 'url': 'report_savings_summary'},
            {'name': 'Collection Summary', 'description': 'Daily collections overview', 'url': 'report_collection_summary'},
            {'name': 'Account Balance', 'description': 'Trial balance and account status', 'url': 'report_account_balance'},
        ]
        return context


class ReportDataMixin:
    """Mixin for common report functionality"""
    
    def get_date_range(self, date_range, start_date=None, end_date=None):
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
    
    def get_branch_filter(self, request):
        branch_id = request.GET.get('branch')
        if request.user.is_superuser and branch_id:
            return Q(branch_id=branch_id)
        elif request.user.branch:
            return Q(branch=request.user.branch)
        return Q()
    
    def get_branch_name_for_export(self, request):
        branch_id = request.GET.get('branch')
        if branch_id and request.user.is_superuser:
            branch = Branch.objects.filter(id=branch_id).first()
            return branch.name if branch else 'all'
        elif request.user.branch:
            return request.user.branch.name
        return 'all'


class MemberSummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView, ReportDataMixin):
    permission_required = 'reports.view_report'
    template_name = 'reports/member_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Member.objects.filter(is_deleted=False)
        branch_filter = self.get_branch_filter(self.request)
        if branch_filter:
            qs = qs.filter(branch_filter)
        
        context['total_members'] = qs.count()
        context['active_members'] = qs.filter(is_active=True).count()
        context['inactive_members'] = qs.filter(is_active=False).count()
        context['members_by_branch'] = qs.values('branch__name').annotate(count=Count('id')).order_by('-count')
        context['form'] = ReportFilterForm(self.request.GET or None)
        return context


class LoanSummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView, ReportDataMixin):
    permission_required = 'reports.view_report'
    template_name = 'reports/loan_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = LoanApplication.objects.all()
        branch_filter = self.get_branch_filter(self.request)
        if branch_filter:
            qs = qs.filter(member__branch__in=[branch_filter])
        
        context['total_loans'] = qs.count()
        context['pending_loans'] = qs.filter(status='pending').count()
        context['approved_loans'] = qs.filter(status='approved').count()
        context['disbursed_loans'] = qs.filter(status='disbursed').count()
        context['closed_loans'] = qs.filter(status='closed').count()
        context['total_applied_amount'] = qs.aggregate(Sum('applied_amount'))['applied_amount__sum'] or 0
        context['total_approved_amount'] = qs.filter(approved_amount__isnull=False).aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0
        context['loans_by_status'] = qs.values('status').annotate(count=Count('id')).order_by('-count')
        context['form'] = ReportFilterForm(self.request.GET or None)
        return context


class SavingsSummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView, ReportDataMixin):
    permission_required = 'reports.view_report'
    template_name = 'reports/savings_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = SavingsAccount.objects.filter(is_deleted=False)
        branch_filter = self.get_branch_filter(self.request)
        if branch_filter:
            qs = qs.filter(member__branch__in=[branch_filter])
        
        context['total_accounts'] = qs.count()
        context['active_accounts'] = qs.filter(is_active=True).count()
        context['inactive_accounts'] = qs.filter(is_active=False).count()
        context['total_balance'] = qs.aggregate(Sum('current_balance'))['current_balance__sum'] or 0
        context['accounts_by_product'] = qs.values('product__name').annotate(
            count=Count('id'),
            total_balance=Sum('current_balance')
        ).order_by('-count')
        context['form'] = ReportFilterForm(self.request.GET or None)
        return context


class CollectionSummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView, ReportDataMixin):
    permission_required = 'reports.view_report'
    template_name = 'reports/collection_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_range = self.request.GET.get('date_range', 'this_month')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        start_date, end_date = self.get_date_range(date_range, start_date_str, end_date_str)
        
        branch_filter = self.get_branch_filter(self.request)
        
        sheet_qs = DailyCollectionSheet.objects.filter(date__range=[start_date, end_date])
        if branch_filter:
            sheet_qs = sheet_qs.filter(branch__in=[branch_filter])
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        context['total_sheets'] = sheet_qs.count()
        context['total_cash'] = sheet_qs.aggregate(Sum('total_cash'))['total_cash__sum'] or 0
        context['verified_sheets'] = sheet_qs.filter(verified=True).count()
        
        entry_qs = CollectionEntry.objects.filter(sheet__date__range=[start_date, end_date])
        if branch_filter:
            entry_qs = entry_qs.filter(sheet__branch__in=[branch_filter])
        context['collections_by_type'] = entry_qs.values('collection_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-count')
        
        context['form'] = ReportFilterForm(self.request.GET or None)
        context['date_range'] = date_range
        return context


class AccountBalanceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView, ReportDataMixin):
    permission_required = 'reports.view_report'
    template_name = 'reports/account_balance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        as_of_date = self.request.GET.get('as_of_date')
        if as_of_date:
            as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
        else:
            as_of_date = timezone.now().date()
        
        branch_filter = self.get_branch_filter(self.request)
        accounts = Account.objects.filter(is_active=True)
        if branch_filter:
            accounts = accounts.filter(Q(branch__in=[branch_filter]) | Q(branch__isnull=True))
        
        account_list = []
        total_debit = 0
        total_credit = 0
        for acc in accounts.order_by('account_type', 'code'):
            items = acc.journalitem_set.filter(entry__date__lte=as_of_date)
            debit = items.aggregate(Sum('debit'))['debit__sum'] or 0
            credit = items.aggregate(Sum('credit'))['credit__sum'] or 0
            account_list.append({
                'code': acc.code,
                'name': acc.name,
                'type': acc.get_account_type_display(),
                'debit': debit,
                'credit': credit,
            })
            total_debit += debit
            total_credit += credit
        
        context['accounts'] = account_list
        context['total_debit'] = total_debit
        context['total_credit'] = total_credit
        context['as_of_date'] = as_of_date
        context['form'] = ReportFilterForm(self.request.GET or None)
        return context


class ReportExportView(LoginRequiredMixin, PermissionRequiredMixin, View, ReportDataMixin):
    permission_required = 'reports.view_report'
    
    def get(self, request, report_type):
        if report_type == 'member_summary':
            return self.export_member_summary(request)
        elif report_type == 'loan_summary':
            return self.export_loan_summary(request)
        elif report_type == 'savings_summary':
            return self.export_savings_summary(request)
        elif report_type == 'collection_summary':
            return self.export_collection_summary(request)
        elif report_type == 'account_balance':
            return self.export_account_balance(request)
        else:
            return HttpResponse('Invalid report type', status=400)
    
    def export_member_summary(self, request):
        qs = Member.objects.filter(is_deleted=False)
        branch_filter = self.get_branch_filter(request)
        if branch_filter:
            qs = qs.filter(branch_filter)
        
        response = HttpResponse(content_type='text/csv')
        branch_name = self.get_branch_name_for_export(request)
        response['Content-Disposition'] = f'attachment; filename="member_summary_{branch_name}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Member ID', 'Name', 'Phone', 'Branch', 'Active', 'Join Date'])
        for m in qs.order_by('member_id'):
            writer.writerow([m.member_id, m.name, m.phone, m.branch.name if m.branch else '', 'Yes' if m.is_active else 'No', m.created_at.date() if hasattr(m, 'created_at') else ''])
        return response
    
    def export_loan_summary(self, request):
        qs = LoanApplication.objects.select_related('member')
        branch_filter = self.get_branch_filter(request)
        if branch_filter:
            qs = qs.filter(member__branch__in=[branch_filter])
        
        response = HttpResponse(content_type='text/csv')
        branch_name = self.get_branch_name_for_export(request)
        response['Content-Disposition'] = f'attachment; filename="loan_summary_{branch_name}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Member', 'Product', 'Applied Amount', 'Approved Amount', 'Status', 'Applied Date', 'Approved Date'])
        for loan in qs.order_by('-applied_date'):
            writer.writerow([loan.member.name, loan.product.name, loan.applied_amount, loan.approved_amount or '', loan.get_status_display(), loan.applied_date, loan.approved_date or ''])
        return response
    
    def export_savings_summary(self, request):
        qs = SavingsAccount.objects.filter(is_deleted=False).select_related('member', 'product')
        branch_filter = self.get_branch_filter(request)
        if branch_filter:
            qs = qs.filter(member__branch__in=[branch_filter])
        
        response = HttpResponse(content_type='text/csv')
        branch_name = self.get_branch_name_for_export(request)
        response['Content-Disposition'] = f'attachment; filename="savings_summary_{branch_name}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Account No', 'Member', 'Product', 'Current Balance', 'Active', 'Opening Date'])
        for acc in qs.order_by('account_no'):
            writer.writerow([acc.account_no, acc.member.name, acc.product.name, acc.current_balance, 'Yes' if acc.is_active else 'No', acc.opening_date])
        return response
    
    def export_collection_summary(self, request):
        date_range = request.GET.get('date_range', 'this_month')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        start_date, end_date = self.get_date_range(date_range, start_date_str, end_date_str)
        
        branch_filter = self.get_branch_filter(request)
        entry_qs = CollectionEntry.objects.filter(sheet__date__range=[start_date, end_date]).select_related('sheet', 'member')
        if branch_filter:
            entry_qs = entry_qs.filter(sheet__branch__in=[branch_filter])
        
        response = HttpResponse(content_type='text/csv')
        branch_name = self.get_branch_name_for_export(request)
        response['Content-Disposition'] = f'attachment; filename="collection_summary_{branch_name}_{start_date}_{end_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Member', 'Type', 'Amount', 'Remark'])
        for e in entry_qs.order_by('-sheet__date'):
            writer.writerow([e.sheet.date, e.member.name, e.get_collection_type_display(), e.amount, e.remark])
        return response
    
    def export_account_balance(self, request):
        as_of_date = request.GET.get('as_of_date')
        if as_of_date:
            as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
        else:
            as_of_date = timezone.now().date()
        
        branch_filter = self.get_branch_filter(request)
        accounts = Account.objects.filter(is_active=True)
        if branch_filter:
            accounts = accounts.filter(Q(branch__in=[branch_filter]) | Q(branch__isnull=True))
        
        response = HttpResponse(content_type='text/csv')
        branch_name = self.get_branch_name_for_export(request)
        response['Content-Disposition'] = f'attachment; filename="trial_balance_{branch_name}_{as_of_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Code', 'Account Name', 'Type', 'Debit', 'Credit'])
        for acc in accounts.order_by('account_type', 'code'):
            items = acc.journalitem_set.filter(entry__date__lte=as_of_date)
            debit = items.aggregate(Sum('debit'))['debit__sum'] or 0
            credit = items.aggregate(Sum('credit'))['credit__sum'] or 0
            writer.writerow([acc.code, acc.name, acc.get_account_type_display(), debit, credit])
        return response