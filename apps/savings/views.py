import json
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from decimal import Decimal
from .models import SavingsProduct, SavingsAccount, SavingsTransaction
from .forms import SavingsProductForm, SavingsAccountForm, SavingsTransactionForm
from erp.utils.tabulator import TabulatorGrid


# ============ DASHBOARD ============

class SavingsDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'savings.view_savingsaccount'
    template_name = 'savings/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accounts = SavingsAccount.objects.filter(is_deleted=False, is_active=True)
        if not self.request.user.is_superuser and self.request.user.branch:
            accounts = accounts.filter(member__branch=self.request.user.branch)

        total_balance = accounts.aggregate(total=models.Sum('current_balance'))['total'] or 0
        total_accounts = accounts.count()
        active_accounts = accounts.filter(is_active=True).count()

        # Last 10 transactions
        transactions = SavingsTransaction.objects.filter(account__in=accounts).order_by('-date')[:10]

        context.update({
            'total_balance': total_balance,
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'recent_transactions': transactions,
        })
        return context


# ============ SAVINGS PRODUCTS ============

class SavingsProductListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'savings.view_savingsproduct'
    template_name = 'savings/product_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Code", "field": "code", "width": 100},
            {"title": "Product Name", "field": "name", "sorter": "string", "widthGrow": 2},
            {"title": "Interest Rate", "field": "interest_rate", "width": 120},
            {"title": "Min Balance", "field": "min_balance", "width": 120},
            {"title": "Status", "field": "is_active", "width": 80},
        ]
        context['columns_json'] = json.dumps(context['columns'])

        products = SavingsProduct.objects.all().order_by('code')
        paginator = Paginator(products, 20)
        page_obj = paginator.get_page(1)

        initial_list = list(page_obj.object_list.values('id', 'code', 'name', 'interest_rate', 'min_balance', 'is_active'))
        for item in initial_list:
            item['is_active'] = 'Active' if item['is_active'] else 'Inactive'

        context['initial_products'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['products'] = products
        return context


class SavingsProductGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'savings.view_savingsproduct'

    def get(self, request):
        queryset = SavingsProduct.objects.all().order_by('code')
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
        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class SavingsProductDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'savings.view_savingsproduct'

    def get(self, request, pk):
        product = SavingsProduct.objects.filter(pk=pk).first()
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        return JsonResponse({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'interest_rate': str(product.interest_rate),
            'min_balance': str(product.min_balance),
            'service_charge': str(product.service_charge),
            'is_active': 'Active' if product.is_active else 'Inactive',
        })


class SavingsProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SavingsProduct
    form_class = SavingsProductForm
    template_name = 'savings/product_form.html'
    success_url = reverse_lazy('savings_product_list')
    permission_required = 'savings.add_savingsproduct'


class SavingsProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SavingsProduct
    form_class = SavingsProductForm
    template_name = 'savings/product_form.html'
    success_url = reverse_lazy('savings_product_list')
    permission_required = 'savings.change_savingsproduct'


class SavingsProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SavingsProduct
    template_name = 'savings/product_confirm_delete.html'
    success_url = reverse_lazy('savings_product_list')
    permission_required = 'savings.delete_savingsproduct'


# ============ SAVINGS ACCOUNTS ============

class SavingsAccountListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'savings.view_savingsaccount'
    template_name = 'savings/account_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Account No", "field": "account_no", "width": 150},
            {"title": "Member", "field": "member_name", "sorter": "string", "widthGrow": 2},
            {"title": "Product", "field": "product_name", "sorter": "string", "widthGrow": 1},
            {"title": "Balance", "field": "current_balance", "width": 120},
        ]
        context['columns_json'] = json.dumps(context['columns'])

        queryset = SavingsAccount.objects.filter(is_deleted=False).select_related('member', 'product')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                queryset = queryset.filter(member__branch=self.request.user.branch)
            else:
                queryset = queryset.none()
                context['branch_missing'] = True

        queryset = queryset.order_by('-opening_date')
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(1)

        initial_list = []
        for account in page_obj.object_list:
            initial_list.append({
                'id': account.id,
                'account_no': account.account_no,
                'member_name': account.member.name,
                'product_name': account.product.name,
                'current_balance': str(account.current_balance),
                'is_active': account.is_active,
            })

        context['initial_accounts'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['accounts'] = queryset
        return context


class SavingsAccountGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'savings.view_savingsaccount'

    def get(self, request):
        queryset = SavingsAccount.objects.filter(is_deleted=False).select_related('member', 'product')
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(member__branch=request.user.branch)
            else:
                queryset = queryset.none()

        account_no_q = request.GET.get('account_no', '').strip()
        member_name_q = request.GET.get('member_name', '').strip()

        if account_no_q:
            queryset = queryset.filter(account_no__icontains=account_no_q)
        if member_name_q:
            queryset = queryset.filter(member__name__icontains=member_name_q)

        grid = TabulatorGrid(request.GET, queryset, search_fields=['account_no', 'member__name'])
        resp = grid.get_response()

        for item in resp.get('data', []):
            account = next((a for a in queryset if a.id == item['id']), None)
            if account:
                item['member_name'] = account.member.name
                item['product_name'] = account.product.name

        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class SavingsAccountDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'savings.view_savingsaccount'

    def get(self, request, pk):
        queryset = SavingsAccount.objects.filter(pk=pk, is_deleted=False).select_related('member', 'product')
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(member__branch=request.user.branch)
            else:
                return JsonResponse({'error': 'Access denied'}, status=403)

        account = queryset.first()
        if not account:
            return JsonResponse({'error': 'Account not found'}, status=404)

        transactions = SavingsTransaction.objects.filter(account=account, is_reversed=False).order_by('-date')[:10]

        return JsonResponse({
            'id': account.id,
            'account_no': account.account_no,
            'member': account.member.name,
            'product': account.product.name,
            'opening_date': str(account.opening_date),
            'current_balance': str(account.current_balance),
            'is_active': 'Active' if account.is_active else 'Inactive',
            'transactions': [
                {
                    'date': str(t.date),
                    'type': t.get_transaction_type_display(),
                    'amount': str(t.amount),
                    'balance': str(t.balance_after),
                }
                for t in transactions
            ]
        })


class SavingsAccountCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SavingsAccount
    form_class = SavingsAccountForm
    template_name = 'savings/account_form.html'
    success_url = reverse_lazy('savings_account_list')
    permission_required = 'savings.add_savingsaccount'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            account = form.save(commit=False)
            account.current_balance = form.cleaned_data['opening_balance']
            account.save()
            # Create opening deposit transaction
            SavingsTransaction.objects.create(
                account=account,
                transaction_type='DEPOSIT',
                amount=account.opening_balance,
                balance_after=account.opening_balance,
                date=account.opening_date,
                description='Initial deposit upon account opening',
                created_by=self.request.user
            )
            return super().form_valid(form)


class SavingsAccountUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SavingsAccount
    form_class = SavingsAccountForm
    template_name = 'savings/account_form.html'
    success_url = reverse_lazy('savings_account_list')
    permission_required = 'savings.change_savingsaccount'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.member.branch != self.request.user.branch:
            raise PermissionError("You cannot edit accounts from other branches")
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class SavingsAccountDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SavingsAccount
    template_name = 'savings/account_confirm_delete.html'
    success_url = reverse_lazy('savings_account_list')
    permission_required = 'savings.delete_savingsaccount'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.member.branch != self.request.user.branch:
            raise PermissionError("You cannot delete accounts from other branches")
        return obj

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_deleted = True
        self.object.is_active = False
        self.object.closed_date = timezone.now().date()
        self.object.save()
        return HttpResponseRedirect(self.success_url)


# ============ SAVINGS TRANSACTIONS ============

class SavingsTransactionListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'savings.view_savingstransaction'
    template_name = 'savings/transaction_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Date", "field": "date", "width": 100},
            {"title": "Account", "field": "account_no", "sorter": "string", "widthGrow": 1},
            {"title": "Member", "field": "member_name", "sorter": "string", "widthGrow": 2},
            {"title": "Type", "field": "transaction_type", "width": 100},
            {"title": "Amount", "field": "amount", "width": 120},
        ]
        context['columns_json'] = json.dumps(context['columns'])

        queryset = SavingsTransaction.objects.filter(is_reversed=False).select_related('account', 'account__member')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                queryset = queryset.filter(account__member__branch=self.request.user.branch)
            else:
                queryset = queryset.none()
                context['branch_missing'] = True

        paginator = Paginator(queryset.order_by('-date'), 20)
        page_obj = paginator.get_page(1)

        initial_list = []
        for t in page_obj.object_list:
            initial_list.append({
                'id': t.id,
                'date': str(t.date),
                'account_no': t.account.account_no,
                'member_name': t.account.member.name,
                'transaction_type': t.get_transaction_type_display(),
                'amount': str(t.amount),
            })

        context['initial_transactions'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['transactions'] = queryset
        return context


class SavingsTransactionGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'savings.view_savingstransaction'

    def get(self, request):
        queryset = SavingsTransaction.objects.filter(is_reversed=False).select_related('account', 'account__member')
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(account__member__branch=request.user.branch)
            else:
                queryset = queryset.none()

        grid = TabulatorGrid(request.GET, queryset, search_fields=['account__account_no', 'account__member__name'])
        resp = grid.get_response()

        for item in resp.get('data', []):
            transaction = next((t for t in queryset if t.id == item['id']), None)
            if transaction:
                item['account_no'] = transaction.account.account_no
                item['member_name'] = transaction.account.member.name
                item['transaction_type'] = transaction.get_transaction_type_display()

        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class SavingsTransactionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SavingsTransaction
    form_class = SavingsTransactionForm
    template_name = 'savings/transaction_form.html'
    success_url = reverse_lazy('savings_transaction_list')
    permission_required = 'savings.add_savingstransaction'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            transaction_obj = form.save(commit=False)
            transaction_obj.created_by = self.request.user
            account = transaction_obj.account
            amount = transaction_obj.amount

            # Calculate new balance
            if transaction_obj.transaction_type == 'DEPOSIT':
                new_balance = account.current_balance + amount
            elif transaction_obj.transaction_type == 'WITHDRAWAL':
                new_balance = account.current_balance - amount
            else:
                new_balance = account.current_balance

            transaction_obj.balance_after = new_balance
            transaction_obj.save()

            # Update account balance
            account.current_balance = new_balance
            account.save()

            return super().form_valid(form)


class SavingsTransactionReverseView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'savings.delete_savingstransaction'

    def post(self, request, pk):
        original = get_object_or_404(SavingsTransaction, pk=pk, is_reversed=False)
        # Permission check
        if not request.user.is_superuser and request.user.branch:
            if original.account.member.branch != request.user.branch:
                return JsonResponse({'error': 'Access denied'}, status=403)

        with transaction.atomic():
            # Create reversal transaction
            reversal_type = 'DEPOSIT' if original.transaction_type == 'WITHDRAWAL' else 'WITHDRAWAL'
            reversal = SavingsTransaction.objects.create(
                account=original.account,
                transaction_type=reversal_type,
                amount=original.amount,
                balance_after=original.account.current_balance + (original.amount if reversal_type == 'DEPOSIT' else -original.amount),
                date=timezone.now().date(),
                description=f'Reversal of transaction #{original.id}',
                created_by=request.user,
                reversed_by=request.user,
                reversed_at=timezone.now(),
                original_transaction=original,
                is_reversed=True
            )
            # Mark original as reversed
            original.is_reversed = True
            original.save()
            # Update account balance
            original.account.current_balance = reversal.balance_after
            original.account.save()

        return JsonResponse({'success': True, 'message': 'Transaction reversed successfully'})


# ============ ACCOUNT STATEMENT PDF ============

class SavingsStatementView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'savings.view_savingsaccount'

    def get(self, request, pk):
        account = get_object_or_404(SavingsAccount, pk=pk, is_deleted=False)
        if not request.user.is_superuser and request.user.branch:
            if account.member.branch != request.user.branch:
                return HttpResponse('Access denied', status=403)

        transactions = SavingsTransaction.objects.filter(account=account, is_reversed=False).order_by('date')
        html_string = render_to_string('savings/statement_pdf.html', {
            'account': account,
            'transactions': transactions,
            'today': timezone.now().date(),
        })
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename=statement_{account.account_no}.pdf'
        HTML(string=html_string).write_pdf(response)
        return response