import json
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from .models import LoanProduct, LoanApplication, LoanDisbursement, LoanInstallmentSchedule
from .forms import (
    LoanProductForm, LoanApplicationForm, LoanApplicationApprovalForm,
    LoanDisbursementForm, LoanInstallmentScheduleForm, LoanDisbursementEditForm, LoanPaymentForm
)
from erp.utils.tabulator import TabulatorGrid


# ============ LOAN PRODUCTS ============

class LoanProductListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'loans.view_loanproduct'
    template_name = 'loans/product_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Code", "field": "code", "width": 120},
            {"title": "Product Name", "field": "name", "sorter": "string", "width": 180},
            {"title": "Interest Rate", "field": "interest_rate", "width": 120},
            {"title": "Min Amount", "field": "min_amount", "width": 120},
            {"title": "Max Amount", "field": "max_amount", "width": 120},
            {"title": "Duration", "field": "duration_months", "width": 100},
            {"title": "Frequency", "field": "installment_frequency", "width": 120},
            {"title": "Processing Fee", "field": "processing_fee", "width": 120},
            {"title": "Late Penalty", "field": "late_penalty_rate", "width": 120},
            {"title": "Status", "field": "is_active", "width": 100},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        products = LoanProduct.objects.all().order_by('code')
        paginator = Paginator(products, 20)
        page_obj = paginator.get_page(1)
        initial_list = list(page_obj.object_list.values(
            'id', 'code', 'name', 'interest_rate', 'min_amount', 'max_amount',
            'duration_months', 'installment_frequency', 'processing_fee', 'late_penalty_rate', 'is_active'
        ))
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


class LoanProductGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'loans.view_loanproduct'

    def get(self, request):
        queryset = LoanProduct.objects.all().order_by('code')
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


class LoanProductDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'loans.view_loanproduct'

    def get(self, request, pk):
        product = LoanProduct.objects.filter(pk=pk).first()
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        return JsonResponse({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'interest_rate': str(product.interest_rate),
            'max_amount': str(product.max_amount),
            'min_amount': str(product.min_amount),
            'duration_months': product.duration_months,
            'installment_frequency': product.get_installment_frequency_display(),
            'processing_fee': str(product.processing_fee),
            'late_penalty_rate': str(product.late_penalty_rate),
            'is_active': 'Active' if product.is_active else 'Inactive',
        })


class LoanProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LoanProduct
    form_class = LoanProductForm
    template_name = 'loans/product_form.html'
    success_url = reverse_lazy('loans_product_list')
    permission_required = 'loans.add_loanproduct'


class LoanProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LoanProduct
    form_class = LoanProductForm
    template_name = 'loans/product_form.html'
    success_url = reverse_lazy('loans_product_list')
    permission_required = 'loans.change_loanproduct'


class LoanProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = LoanProduct
    template_name = 'loans/product_confirm_delete.html'
    success_url = reverse_lazy('loans_product_list')
    permission_required = 'loans.delete_loanproduct'


# ============ LOAN APPLICATIONS ============

class LoanApplicationListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'loans.view_loanapplication'
    template_name = 'loans/application_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Member ID", "field": "member_id", "sorter": "string", "width": 120},
            {"title": "Member", "field": "member_name", "sorter": "string", "widthGrow": 2},
            {"title": "Product", "field": "product_name", "sorter": "string", "widthGrow": 1},
            {"title": "Applied Amount", "field": "applied_amount", "width": 120},
            {"title": "Status", "field": "status", "width": 100},
            {"title": "Date", "field": "applied_date", "width": 100},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        queryset = LoanApplication.objects.select_related('member', 'product')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                queryset = queryset.filter(member__branch=self.request.user.branch)
            else:
                queryset = queryset.none()
                context['branch_missing'] = True
        queryset = queryset.order_by('-applied_date')
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(1)
        initial_list = []
        for app in page_obj.object_list:
            initial_list.append({
                'id': app.id,
                'member_id': app.member.member_id,
                'member_name': app.member.name,
                'product_name': app.product.name,
                'applied_amount': str(app.applied_amount),
                'status': app.get_status_display(),
                'applied_date': str(app.applied_date),
            })
        context['initial_applications'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['applications'] = queryset
        return context


class LoanApplicationGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'loans.view_loanapplication'

    def get(self, request):
        queryset = LoanApplication.objects.select_related('member', 'product')
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(member__branch=request.user.branch)
            else:
                queryset = queryset.none()
        member_id_q = request.GET.get('member_id', '').strip()
        member_name_q = request.GET.get('member_name', '').strip()
        status_q = request.GET.get('status', '').strip()
        if member_id_q:
            queryset = queryset.filter(member__member_id__icontains=member_id_q)
        if member_name_q:
            queryset = queryset.filter(member__name__icontains=member_name_q)
        if status_q:
            queryset = queryset.filter(status=status_q)
        grid = TabulatorGrid(request.GET, queryset, search_fields=['member__name', 'member__member_id', 'status'])
        resp = grid.get_response()
        for item in resp.get('data', []):
            app = next((a for a in queryset if a.id == item['id']), None)
            if app:
                item['member_id'] = app.member.member_id
                item['member_name'] = app.member.name
                item['product_name'] = app.product.name
                item['status'] = app.get_status_display()
        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class LoanApplicationDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'loans.view_loanapplication'

    def get(self, request, pk):
        queryset = LoanApplication.objects.select_related('member', 'product', 'approved_by')
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(member__branch=request.user.branch)
            else:
                return JsonResponse({'error': 'Access denied'}, status=403)
        app = queryset.filter(pk=pk).first()
        if not app:
            return JsonResponse({'error': 'Application not found'}, status=404)
        schedules = LoanInstallmentSchedule.objects.filter(loan=app).order_by('installment_no')
        return JsonResponse({
            'id': app.id,
            'member': app.member.name,
            'product': app.product.name,
            'applied_amount': str(app.applied_amount),
            'approved_amount': str(app.approved_amount) if app.approved_amount else 'N/A',
            'duration': app.duration,
            'purpose': app.purpose,
            'status': app.get_status_display(),
            'applied_date': str(app.applied_date),
            'approved_date': str(app.approved_date) if app.approved_date else 'N/A',
            'schedules': [
                {
                    'installment_no': s.installment_no,
                    'due_date': str(s.due_date),
                    'principal': str(s.principal_amount),
                    'interest': str(s.interest_amount),
                    'total_due': str(s.total_due),
                    'paid': 'Yes' if s.is_paid else 'No',
                }
                for s in schedules[:10]
            ]
        })


class LoanApplicationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LoanApplication
    form_class = LoanApplicationForm
    template_name = 'loans/application_form.html'
    success_url = reverse_lazy('loans_application_list')
    permission_required = 'loans.add_loanapplication'


class LoanApplicationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LoanApplication
    form_class = LoanApplicationApprovalForm
    template_name = 'loans/application_form.html'
    success_url = reverse_lazy('loans_application_list')
    permission_required = 'loans.change_loanapplication'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.member.branch != self.request.user.branch:
            raise PermissionError("You cannot edit applications from other branches")
        return obj

    def form_valid(self, form):
        form.instance.approved_by = self.request.user
        return super().form_valid(form)


class LoanApplicationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = LoanApplication
    template_name = 'loans/application_confirm_delete.html'
    success_url = reverse_lazy('loans_application_list')
    permission_required = 'loans.delete_loanapplication'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.member.branch != self.request.user.branch:
            raise PermissionError("You cannot delete applications from other branches")
        return obj


# ============ LOAN DISBURSEMENTS ============

class LoanDisbursementListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'loans.view_loandisbursement'
    template_name = 'loans/disbursement_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Date", "field": "disbursement_date", "width": 100},
            {"title": "Member", "field": "member_name", "sorter": "string", "widthGrow": 2},
            {"title": "Amount", "field": "amount", "width": 120},
            {"title": "Method", "field": "method", "width": 100},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        queryset = LoanDisbursement.objects.select_related('loan', 'loan__member')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                queryset = queryset.filter(loan__member__branch=self.request.user.branch)
            else:
                queryset = queryset.none()
                context['branch_missing'] = True
        queryset = queryset.order_by('-disbursement_date')
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(1)
        initial_list = []
        for d in page_obj.object_list:
            initial_list.append({
                'id': d.id,
                'disbursement_date': str(d.disbursement_date),
                'member_name': d.loan.member.name,
                'amount': str(d.amount),
                'method': d.method,
            })
        context['initial_disbursements'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['disbursements'] = queryset
        return context


class LoanDisbursementGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'loans.view_loandisbursement'

    def get(self, request):
        queryset = LoanDisbursement.objects.select_related('loan', 'loan__member')
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(loan__member__branch=request.user.branch)
            else:
                queryset = queryset.none()
        grid = TabulatorGrid(request.GET, queryset, search_fields=['loan__member__name', 'method'])
        resp = grid.get_response()
        for item in resp.get('data', []):
            disbursement = next((d for d in queryset if d.id == item['id']), None)
            if disbursement:
                item['member_name'] = disbursement.loan.member.name
        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class LoanDisbursementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LoanDisbursement
    form_class = LoanDisbursementForm
    template_name = 'loans/disbursement_form.html'
    success_url = reverse_lazy('loans_disbursement_list')
    permission_required = 'loans.add_loandisbursement'

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            disbursement = self.object
            loan_app = disbursement.loan
            loan_app.status = 'disbursed'
            loan_app.disbursement_date = disbursement.disbursement_date
            loan_app.save()
            loan_app.generate_schedule(disbursement.disbursement_date)
            return response


class LoanDisbursementEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LoanDisbursement
    form_class = LoanDisbursementEditForm
    template_name = 'loans/disbursement_edit_form.html'
    success_url = reverse_lazy('loans_disbursement_list')
    permission_required = 'loans.change_loandisbursement'

    def form_valid(self, form):
        with transaction.atomic():
            old_amount = self.get_object().amount
            response = super().form_valid(form)
            disbursement = self.object
            if old_amount != disbursement.amount:
                # Update loan approved_amount to match new disbursed amount
                loan_app = disbursement.loan
                loan_app.approved_amount = disbursement.amount
                loan_app.save()
                loan_app.generate_schedule(disbursement.disbursement_date)
            return response


# ============ LOAN INSTALLMENT SCHEDULES ============

class LoanInstallmentScheduleListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'loans.view_loaninstallmentschedule'
    template_name = 'loans/schedule_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Member", "field": "member_name", "sorter": "string", "widthGrow": 2},
            {"title": "Installment", "field": "installment_no", "width": 100},
            {"title": "Due Date", "field": "due_date", "width": 100},
            {"title": "Total Due", "field": "total_due", "width": 100},
            {"title": "Paid", "field": "is_paid", "width": 80},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        queryset = LoanInstallmentSchedule.objects.select_related('loan', 'loan__member')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                queryset = queryset.filter(loan__member__branch=self.request.user.branch)
            else:
                queryset = queryset.none()
                context['branch_missing'] = True
        queryset = queryset.order_by('-due_date')
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(1)
        initial_list = []
        for s in page_obj.object_list:
            initial_list.append({
                'id': s.id,
                'member_name': s.loan.member.name,
                'installment_no': s.installment_no,
                'due_date': str(s.due_date),
                'principal_amount': str(s.principal_amount),
                'interest_amount': str(s.interest_amount),
                'total_due': str(s.total_due),
                'paid_total': str(s.paid_total),
                'is_paid': 'Yes' if s.is_paid else 'No',
            })
        context['initial_schedules'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['schedules'] = queryset
        return context


class LoanInstallmentScheduleGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'loans.view_loaninstallmentschedule'

    def get(self, request):
        queryset = LoanInstallmentSchedule.objects.select_related('loan', 'loan__member')
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(loan__member__branch=request.user.branch)
            else:
                queryset = queryset.none()
        grid = TabulatorGrid(request.GET, queryset, search_fields=['loan__member__name'])
        resp = grid.get_response()
        for item in resp.get('data', []):
            schedule = next((s for s in queryset if s.id == item['id']), None)
            if schedule:
                item['member_name'] = schedule.loan.member.name
                item['is_paid'] = 'Yes' if schedule.is_paid else 'No'
        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class LoanInstallmentScheduleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LoanInstallmentSchedule
    form_class = LoanInstallmentScheduleForm
    template_name = 'loans/schedule_form.html'
    success_url = reverse_lazy('loans_schedule_list')
    permission_required = 'loans.change_loaninstallmentschedule'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.loan.member.branch != self.request.user.branch:
            raise PermissionError("You cannot edit schedules from other branches")
        return obj


class LoanPaymentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'loans.change_loaninstallmentschedule'

    def get(self, request, pk):
        from django.template.loader import render_to_string
        schedule = get_object_or_404(LoanInstallmentSchedule, pk=pk)
        if not request.user.is_superuser and request.user.branch:
            if schedule.loan.member.branch != request.user.branch:
                return JsonResponse({'error': 'Access denied'}, status=403)
        form = LoanPaymentForm(initial={'payment_date': timezone.now().date()})
        form_html = render_to_string('loans/_payment_form.html', {'form': form, 'schedule_id': pk})
        return JsonResponse({
            'installment_no': schedule.installment_no,
            'member_name': schedule.loan.member.name,
            'total_due': str(schedule.total_due),
            'paid_total': str(schedule.paid_total),
            'remaining_due': str(schedule.total_due - schedule.paid_total),
            'due_date': str(schedule.due_date),
            'late_fee': str(schedule.late_fee),
            'form_html': form_html,
        })

    def post(self, request, pk):
        schedule = get_object_or_404(LoanInstallmentSchedule, pk=pk)
        if not request.user.is_superuser and request.user.branch:
            if schedule.loan.member.branch != request.user.branch:
                return JsonResponse({'error': 'Access denied'}, status=403)
        form = LoanPaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_date = form.cleaned_data['payment_date'] or timezone.now().date()
            success, message = schedule.make_payment(amount, payment_date)
            if success:
                return JsonResponse({'success': True, 'message': message})
            else:
                return JsonResponse({'success': False, 'error': message}, status=400)
        else:
            return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)