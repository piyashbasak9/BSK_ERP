import json
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Account, JournalEntry, JournalItem
from .forms import AccountForm, JournalEntryForm, JournalItemFormSet
from erp.utils.tabulator import TabulatorGrid


# ============ ACCOUNTS ============

class AccountListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'accounting.view_account'
    template_name = 'accounting/account_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Code", "field": "code", "width": 100},
            {"title": "Account Name", "field": "name", "sorter": "string", "widthGrow": 2},
            {"title": "Type", "field": "account_type", "width": 120},
            {"title": "Status", "field": "is_active", "width": 80},
        ]
        context['columns_json'] = json.dumps(context['columns'])

        accounts = Account.objects.all().order_by('code')
        if not self.request.user.is_superuser and self.request.user.branch:
            accounts = accounts.filter(branch=self.request.user.branch)

        paginator = Paginator(accounts, 20)
        page_obj = paginator.get_page(1)

        initial_list = list(page_obj.object_list.values(
            'id', 'code', 'name', 'account_type', 'is_active'
        ))
        for item in initial_list:
            item['is_active'] = 'Active' if item['is_active'] else 'Inactive'

        context['initial_accounts'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['accounts'] = accounts
        return context


class AccountGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'accounting.view_account'

    def get(self, request):
        queryset = Account.objects.all().order_by('code')
        if not request.user.is_superuser and request.user.branch:
            queryset = queryset.filter(branch=request.user.branch)

        code_q = request.GET.get('code', '').strip()
        name_q = request.GET.get('name', '').strip()
        if code_q:
            queryset = queryset.filter(code__icontains=code_q)
        if name_q:
            queryset = queryset.filter(name__icontains=name_q)

        grid = TabulatorGrid(request.GET, queryset, search_fields=['code', 'name'])
        resp = grid.get_response()
        for item in resp.get('data', []):
            item['is_active'] = 'Active' if item['is_active'] else 'Inactive'
        return JsonResponse(resp)


class AccountDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'accounting.view_account'

    def get(self, request, pk):
        account = Account.objects.filter(pk=pk).first()
        if not account:
            return JsonResponse({'error': 'Account not found'}, status=404)
        if not request.user.is_superuser and account.branch and account.branch != request.user.branch:
            return JsonResponse({'error': 'Access denied'}, status=403)
        return JsonResponse({
            'id': account.id,
            'code': account.code,
            'name': account.name,
            'account_type': account.get_account_type_display(),
            'parent': account.parent.name if account.parent else 'None',
            'is_active': 'Active' if account.is_active else 'Inactive',
        })


class AccountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounting/account_form.html'
    success_url = reverse_lazy('account_list')
    permission_required = 'accounting.add_account'


class AccountUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounting/account_form.html'
    success_url = reverse_lazy('account_list')
    permission_required = 'accounting.change_account'


class AccountDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Account
    template_name = 'accounting/account_confirm_delete.html'
    success_url = reverse_lazy('account_list')
    permission_required = 'accounting.delete_account'


# ============ JOURNAL ENTRIES ============

class JournalEntryListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'accounting.view_journalentry'
    template_name = 'accounting/journalentry_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Voucher No", "field": "voucher_no", "width": 120},
            {"title": "Date", "field": "date", "width": 100},
            {"title": "Description", "field": "description", "sorter": "string", "widthGrow": 2},
            {"title": "Posted", "field": "is_posted", "width": 80},
        ]
        context['columns_json'] = json.dumps(context['columns'])

        entries = JournalEntry.objects.all().order_by('-date')
        if not self.request.user.is_superuser and self.request.user.branch:
            entries = entries.filter(branch=self.request.user.branch)

        paginator = Paginator(entries, 20)
        page_obj = paginator.get_page(1)

        initial_list = list(page_obj.object_list.values('id', 'voucher_no', 'date', 'description', 'is_posted'))
        for item in initial_list:
            item['is_posted'] = 'Yes' if item['is_posted'] else 'No'

        context['initial_entries'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        return context


class JournalEntryGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'accounting.view_journalentry'

    def get(self, request):
        queryset = JournalEntry.objects.all().order_by('-date')
        if not request.user.is_superuser and request.user.branch:
            queryset = queryset.filter(branch=request.user.branch)

        voucher_q = request.GET.get('voucher_no', '').strip()
        if voucher_q:
            queryset = queryset.filter(voucher_no__icontains=voucher_q)

        grid = TabulatorGrid(request.GET, queryset, search_fields=['voucher_no', 'description'])
        resp = grid.get_response()
        for item in resp.get('data', []):
            item['is_posted'] = 'Yes' if item['is_posted'] else 'No'
        return JsonResponse(resp)


class JournalEntryDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'accounting.view_journalentry'

    def get(self, request, pk):
        entry = JournalEntry.objects.filter(pk=pk).first()
        if not entry:
            return JsonResponse({'error': 'Journal entry not found'}, status=404)
        if not request.user.is_superuser and entry.branch != request.user.branch:
            return JsonResponse({'error': 'Access denied'}, status=403)
        items = entry.items.all().values('account__code', 'account__name', 'debit', 'credit')
        return JsonResponse({
            'id': entry.id,
            'voucher_no': entry.voucher_no,
            'date': str(entry.date),
            'description': entry.description,
            'is_posted': 'Yes' if entry.is_posted else 'No',
            'items': list(items),
        })


class JournalEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'accounting/journalentry_form.html'
    success_url = reverse_lazy('journalentry_list')
    permission_required = 'accounting.add_journalentry'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = JournalItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = JournalItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            self.object.save()
            formset.instance = self.object
            formset.save()
            # Check debit/credit balance
            total_debit = sum(item.debit for item in self.object.items.all())
            total_credit = sum(item.credit for item in self.object.items.all())
            if total_debit != total_credit:
                form.add_error(None, f'Total debit ({total_debit}) does not equal total credit ({total_credit})')
                return self.form_invalid(form)
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class JournalEntryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'accounting/journalentry_form.html'
    success_url = reverse_lazy('journalentry_list')
    permission_required = 'accounting.change_journalentry'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = JournalItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = JournalItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            total_debit = sum(item.debit for item in self.object.items.all())
            total_credit = sum(item.credit for item in self.object.items.all())
            if total_debit != total_credit:
                form.add_error(None, f'Total debit ({total_debit}) does not equal total credit ({total_credit})')
                return self.form_invalid(form)
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class JournalEntryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = JournalEntry
    template_name = 'accounting/journalentry_confirm_delete.html'
    success_url = reverse_lazy('journalentry_list')
    permission_required = 'accounting.delete_journalentry'


class JournalEntryReverseView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'accounting.add_journalentry'

    def post(self, request, pk):
        original = get_object_or_404(JournalEntry, pk=pk)
        if not request.user.is_superuser and original.branch != request.user.branch:
            return JsonResponse({'error': 'Access denied'}, status=403)

        # Create reversal entry
        reversal = JournalEntry.objects.create(
            voucher_no=f'REV-{original.voucher_no}',
            date=timezone.now().date(),
            description=f'Reversal of {original.voucher_no}: {original.description}',
            branch=original.branch,
            created_by=request.user,
            is_posted=True
        )
        for item in original.items.all():
            JournalItem.objects.create(
                entry=reversal,
                account=item.account,
                debit=item.credit,
                credit=item.debit,
                reference_no=f'Rev-{item.reference_no}' if item.reference_no else ''
            )
        return JsonResponse({'success': True, 'message': 'Reversal entry created successfully'})