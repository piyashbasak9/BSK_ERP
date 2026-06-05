from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from apps.members.models import Member
from apps.loans.models import LoanApplication
from apps.savings.models import SavingsAccount
from apps.collections.models import CollectionEntry
from apps.accounting.models import Account, JournalItem
from django.utils import timezone
from datetime import timedelta

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        branch = user.branch
        today = timezone.now().date()

        # Total members
        members_qs = Member.objects.filter(is_deleted=False)
        if branch and not user.is_superuser:
            members_qs = members_qs.filter(branch=branch)
        context['total_members'] = members_qs.count()

        # Active loans
        loans_qs = LoanApplication.objects.filter(status='disbursed', closed_date__isnull=True)
        if branch and not user.is_superuser:
            loans_qs = loans_qs.filter(member__branch=branch)
        context['active_loans'] = loans_qs.count()

        # Savings balance
        savings_qs = SavingsAccount.objects.filter(is_active=True)
        if branch and not user.is_superuser:
            savings_qs = savings_qs.filter(member__branch=branch)
        context['savings_balance'] = savings_qs.aggregate(Sum('current_balance'))['current_balance__sum'] or 0

        # Daily collection
        collection_qs = CollectionEntry.objects.filter(sheet__date=today)
        if branch and not user.is_superuser:
            collection_qs = collection_qs.filter(sheet__branch=branch)
        context['daily_collection'] = collection_qs.aggregate(Sum('amount'))['amount__sum'] or 0

        # Cash position (simplified: cash account balance for branch)
        cash_account = Account.objects.filter(code='1020')
        if branch and not user.is_superuser:
            cash_account = cash_account.filter(branch=branch)
        cash_account = cash_account.first()
        if cash_account:
            cash_debit = JournalItem.objects.filter(account=cash_account).aggregate(Sum('debit'))['debit__sum'] or 0
            cash_credit = JournalItem.objects.filter(account=cash_account).aggregate(Sum('credit'))['credit__sum'] or 0
            context['cash_position'] = cash_debit - cash_credit
        else:
            context['cash_position'] = 0

        return context