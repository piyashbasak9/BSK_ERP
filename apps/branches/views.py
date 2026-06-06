import json
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from .models import Branch
from .forms import BranchForm
from erp.utils.tabulator import TabulatorGrid
from django.core.paginator import Paginator


class BranchListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """List all branches with master-detail interface"""
    permission_required = 'branches.view_branch'
    template_name = 'branches/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Code", "field": "code", "width": 100},
            {"title": "Branch Name", "field": "name", "sorter": "string", "widthGrow": 2},
            {"title": "Phone", "field": "phone", "widthGrow": 1},
            {"title": "Status", "field": "is_active", "width": 80},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        
        branches = Branch.objects.all().order_by('code')
        paginator = Paginator(branches, 20)
        page_obj = paginator.get_page(1)
        
        initial_list = list(page_obj.object_list.values(
            'id', 'code', 'name', 'phone', 'is_active'
        ))
        # Convert boolean to display value
        for item in initial_list:
            item['is_active'] = 'Active' if item['is_active'] else 'Inactive'
        
        context['initial_branches'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['branches'] = branches
        return context


class BranchGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """AJAX endpoint for branch data with pagination"""
    permission_required = 'branches.view_branch'

    def get(self, request):
        queryset = Branch.objects.all().order_by('code')
        
        # Support field filtering
        code_q = request.GET.get('code', '').strip()
        name_q = request.GET.get('name', '').strip()
        phone_q = request.GET.get('phone', '').strip()
        
        if code_q:
            queryset = queryset.filter(code__icontains=code_q)
        if name_q:
            queryset = queryset.filter(name__icontains=name_q)
        if phone_q:
            queryset = queryset.filter(phone__icontains=phone_q)

        grid = TabulatorGrid(request.GET, queryset, search_fields=['code', 'name', 'phone'])
        resp = grid.get_response()
        
        # Convert is_active to display value
        for item in resp.get('data', []):
            item['is_active'] = 'Active' if item['is_active'] else 'Inactive'
        
        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class BranchDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """AJAX endpoint for branch detail"""
    permission_required = 'branches.view_branch'

    def get(self, request, pk):
        branch = Branch.objects.filter(pk=pk).first()
        if not branch:
            return JsonResponse({'error': 'Branch not found'}, status=404)
        
        return JsonResponse({
            'id': branch.id,
            'code': branch.code,
            'name': branch.name,
            'address': branch.address,
            'phone': branch.phone,
            'email': branch.email,
            'opening_date': branch.opening_date,
            'is_active': 'Active' if branch.is_active else 'Inactive',
        })


class BranchCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new branch"""
    model = Branch
    form_class = BranchForm
    template_name = 'branches/form.html'
    success_url = reverse_lazy('branch_list')
    permission_required = 'branches.add_branch'


class BranchUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update existing branch"""
    model = Branch
    form_class = BranchForm
    template_name = 'branches/form.html'
    success_url = reverse_lazy('branch_list')
    permission_required = 'branches.change_branch'


class BranchDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete branch"""
    model = Branch
    template_name = 'branches/confirm_delete.html'
    success_url = reverse_lazy('branch_list')
    permission_required = 'branches.delete_branch'


class BranchDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View branch details"""
    model = Branch
    template_name = 'branches/detail.html'
    permission_required = 'branches.view_branch'
