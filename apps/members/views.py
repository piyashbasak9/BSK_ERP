import json
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Member
from .forms import MemberForm
from erp.utils.tabulator import TabulatorGrid
from erp.utils.middleware import get_current_user, get_current_ip
from django.core.paginator import Paginator

class MemberListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'members.view_member'
    template_name = 'members/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Member ID", "field": "member_id", "width": 150},
            {"title": "Name", "field": "name", "sorter": "string", "widthGrow": 2},
            {"title": "Phone", "field": "phone", "widthGrow": 1},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        members = Member.objects.filter(is_deleted=False).select_related('branch').order_by('member_id')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                members = members.filter(branch=self.request.user.branch)
            else:
                members = members.none()
                context['branch_missing'] = True
        # provide a server-side initial page of data for immediate rendering (fallback)
        paginator = Paginator(members, 20)
        page_obj = paginator.get_page(1)
        initial_list = list(page_obj.object_list.values('id', 'member_id', 'name', 'phone'))
        context['initial_members'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
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
        # support specific field filtering from separate search inputs
        member_id_q = request.GET.get('member_id', '').strip()
        name_q = request.GET.get('name', '').strip()
        phone_q = request.GET.get('phone', '').strip()
        if member_id_q:
            queryset = queryset.filter(member_id__icontains=member_id_q)
        if name_q:
            queryset = queryset.filter(name__icontains=name_q)
        if phone_q:
            queryset = queryset.filter(phone__icontains=phone_q)

        grid = TabulatorGrid(request.GET, queryset, search_fields=['member_id', 'name', 'phone'])
        resp = grid.get_response()
        # echo received GET params to help client-side debugging
        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)

class MemberDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'members.view_member'

    def get(self, request, pk):
        queryset = Member.objects.filter(pk=pk, is_deleted=False).select_related('branch', 'created_by')
        
        # Security: Filter by branch for non-superusers
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(branch=request.user.branch)
            else:
                return JsonResponse({'error': 'Access denied'}, status=403)
        
        member = queryset.first()
        if not member:
            return JsonResponse({'error': 'Member not found'}, status=404)
        
        return JsonResponse({
            'id': member.id,
            'member_id': member.member_id,
            'name': member.name,
            'father_name': member.father_name,
            'mother_name': member.mother_name,
            'spouse_name': member.spouse_name,
            'gender': member.get_gender_display(),
            'marital_status': member.marital_status,
            'date_of_birth': member.date_of_birth,
            'nid': member.nid,
            'phone': member.phone,
            'email': member.email,
            'present_address': member.present_address,
            'permanent_address': member.permanent_address,
            'photo': member.photo.url if member.photo else None,
            'branch': member.branch.name if member.branch else None,
            'registration_date': member.registration_date,
            'is_active': member.is_active,
            'created_by': str(member.created_by) if member.created_by else None,
            'created_at': member.created_at,
            'updated_at': member.updated_at,
        })

class MemberCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = 'members/form.html'
    success_url = reverse_lazy('member_list')
    permission_required = 'members.add_member'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class MemberUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = 'members/form.html'
    success_url = reverse_lazy('member_list')
    permission_required = 'members.change_member'
    
    def get_object(self, queryset=None):
        """Override to ensure user can only edit members in their branch"""
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.branch != self.request.user.branch:
            raise PermissionError("You cannot edit members from other branches")
        return obj

class MemberDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Member
    template_name = 'members/confirm_delete.html'
    success_url = reverse_lazy('member_list')
    permission_required = 'members.delete_member'
    
    def get_object(self, queryset=None):
        """Override to ensure user can only delete members in their branch"""
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.branch != self.request.user.branch:
            raise PermissionError("You cannot delete members from other branches")
        return obj
    
    def delete(self, request, *args, **kwargs):
        """Override to use soft delete instead of hard delete"""
        self.object = self.get_object()
        self.object.is_deleted = True
        self.object.deleted_at = timezone.now()
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

class MemberDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Member
    template_name = 'members/detail.html'
    permission_required = 'members.view_member'
    
    def get_object(self, queryset=None):
        """Override to ensure user can only view members in their branch"""
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.branch != self.request.user.branch:
            raise PermissionError("You cannot view members from other branches")
        return obj
