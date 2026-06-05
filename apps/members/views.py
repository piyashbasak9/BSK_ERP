import json

from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from .models import Member
from erp.utils.tabulator import TabulatorGrid
from erp.utils.middleware import get_current_user, get_current_ip

class MemberListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'members.view_member'
    template_name = 'members/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "ID", "field": "member_id", "width": 100},
            {"title": "Name", "field": "name", "sorter": "string"},
            {"title": "Phone", "field": "phone"},
            {"title": "Registration Date", "field": "registration_date", "sorter": "date"},
            {"title": "Status", "field": "is_active", "formatter": "tickCross"},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        members = Member.objects.filter(is_deleted=False).select_related('branch').order_by('member_id')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                members = members.filter(branch=self.request.user.branch)
            else:
                members = members.none()
                context['branch_missing'] = True
        context['members'] = members
        return context

class MemberGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'members.view_member'

    def get(self, request):
        queryset = Member.objects.filter(is_deleted=False)
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(branch=request.user.branch)
            else:
                queryset = queryset.none()
        grid = TabulatorGrid(request.GET, queryset, search_fields=['member_id', 'name', 'phone'])
        return JsonResponse(grid.get_response())

class MemberCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Member
    fields = [
        'branch', 'member_id', 'name', 'father_name', 'mother_name', 'spouse_name',
        'gender', 'marital_status', 'date_of_birth', 'nid', 'phone', 'email',
        'present_address', 'permanent_address', 'photo',
    ]
    template_name = 'members/form.html'
    success_url = reverse_lazy('member_list')
    permission_required = 'members.add_member'

class MemberUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Member
    fields = [
        'branch', 'member_id', 'name', 'father_name', 'mother_name', 'spouse_name',
        'gender', 'marital_status', 'date_of_birth', 'nid', 'phone', 'email',
        'present_address', 'permanent_address', 'photo',
    ]
    template_name = 'members/form.html'
    success_url = reverse_lazy('member_list')
    permission_required = 'members.change_member'

class MemberDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Member
    template_name = 'members/confirm_delete.html'
    success_url = reverse_lazy('member_list')
    permission_required = 'members.delete_member'

class MemberDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Member
    template_name = 'members/detail.html'
    permission_required = 'members.view_member'
