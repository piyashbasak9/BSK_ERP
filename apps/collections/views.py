import json
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from .models import DailyCollectionSheet, CollectionEntry
from .forms import DailyCollectionSheetForm, CollectionEntryForm
from erp.utils.tabulator import TabulatorGrid


# ============ DAILY COLLECTION SHEETS ============

class DailyCollectionSheetListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """List all daily collection sheets with master-detail interface"""
    permission_required = 'collections.view_dailycollectionsheet'
    template_name = 'collections/sheet_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Date", "field": "date", "width": 100},
            {"title": "Branch", "field": "branch_name", "sorter": "string", "widthGrow": 1},
            {"title": "Collector", "field": "collector_name", "sorter": "string", "widthGrow": 1},
            {"title": "Total Cash", "field": "total_cash", "width": 120},
            {"title": "Verified", "field": "verified", "width": 80},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        
        queryset = DailyCollectionSheet.objects.select_related('branch', 'collector')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                queryset = queryset.filter(branch=self.request.user.branch)
            else:
                queryset = queryset.none()
                context['branch_missing'] = True
        
        queryset = queryset.order_by('-date')
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(1)
        
        initial_list = []
        for sheet in page_obj.object_list:
            initial_list.append({
                'id': sheet.id,
                'date': str(sheet.date),
                'branch_name': sheet.branch.name,
                'collector_name': sheet.collector.username,
                'total_cash': str(sheet.total_cash),
                'verified': 'Yes' if sheet.verified else 'No',
            })
        
        context['initial_sheets'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['sheets'] = queryset
        return context


class DailyCollectionSheetGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """AJAX endpoint for collection sheet data"""
    permission_required = 'collections.view_dailycollectionsheet'

    def get(self, request):
        queryset = DailyCollectionSheet.objects.select_related('branch', 'collector')
        
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(branch=request.user.branch)
            else:
                queryset = queryset.none()
        
        date_q = request.GET.get('date', '').strip()
        branch_q = request.GET.get('branch_name', '').strip()
        
        if date_q:
            queryset = queryset.filter(date=date_q)
        if branch_q:
            queryset = queryset.filter(branch__name__icontains=branch_q)

        grid = TabulatorGrid(request.GET, queryset, search_fields=['date', 'branch__name'])
        resp = grid.get_response()
        
        for item in resp.get('data', []):
            sheet = next((s for s in queryset if s.id == item['id']), None)
            if sheet:
                item['branch_name'] = sheet.branch.name
                item['collector_name'] = sheet.collector.username
                item['verified'] = 'Yes' if sheet.verified else 'No'
        
        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class DailyCollectionSheetDetailJsonView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """AJAX endpoint for collection sheet detail"""
    permission_required = 'collections.view_dailycollectionsheet'

    def get(self, request, pk):
        queryset = DailyCollectionSheet.objects.select_related('branch', 'collector', 'verified_by')
        
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(branch=request.user.branch)
            else:
                return JsonResponse({'error': 'Access denied'}, status=403)
        
        sheet = queryset.filter(pk=pk).first()
        if not sheet:
            return JsonResponse({'error': 'Sheet not found'}, status=404)
        
        entries = CollectionEntry.objects.filter(sheet=sheet).select_related('member')
        
        return JsonResponse({
            'id': sheet.id,
            'date': str(sheet.date),
            'branch': sheet.branch.name,
            'collector': sheet.collector.username,
            'total_cash': str(sheet.total_cash),
            'verified': 'Yes' if sheet.verified else 'No',
            'verified_by': sheet.verified_by.username if sheet.verified_by else 'N/A',
            'entry_count': entries.count(),
            'entries': [
                {
                    'member': e.member.name,
                    'type': e.get_collection_type_display(),
                    'amount': str(e.amount),
                }
                for e in entries[:20]
            ]
        })


class DailyCollectionSheetCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new daily collection sheet"""
    model = DailyCollectionSheet
    form_class = DailyCollectionSheetForm
    template_name = 'collections/sheet_form.html'
    success_url = reverse_lazy('collections_sheet_list')
    permission_required = 'collections.add_dailycollectionsheet'
    
    def form_valid(self, form):
        form.instance.collector = self.request.user
        return super().form_valid(form)


class DailyCollectionSheetUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update daily collection sheet"""
    model = DailyCollectionSheet
    form_class = DailyCollectionSheetForm
    template_name = 'collections/sheet_form.html'
    success_url = reverse_lazy('collections_sheet_list')
    permission_required = 'collections.change_dailycollectionsheet'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and obj.branch != self.request.user.branch:
            raise PermissionError("You cannot edit sheets from other branches")
        return obj


# ============ COLLECTION ENTRIES ============

class CollectionEntryListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """List all collection entries with master-detail interface"""
    permission_required = 'collections.view_collectionentry'
    template_name = 'collections/entry_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Date", "field": "date", "width": 100},
            {"title": "Member", "field": "member_name", "sorter": "string", "widthGrow": 2},
            {"title": "Type", "field": "collection_type", "width": 100},
            {"title": "Amount", "field": "amount", "width": 120},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        
        queryset = CollectionEntry.objects.select_related('sheet', 'member')
        if not self.request.user.is_superuser:
            if self.request.user.branch:
                queryset = queryset.filter(sheet__branch=self.request.user.branch)
            else:
                queryset = queryset.none()
                context['branch_missing'] = True
        
        queryset = queryset.order_by('-sheet__date')
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(1)
        
        initial_list = []
        for entry in page_obj.object_list:
            initial_list.append({
                'id': entry.id,
                'date': str(entry.sheet.date),
                'member_name': entry.member.name,
                'collection_type': entry.get_collection_type_display(),
                'amount': str(entry.amount),
            })
        
        context['initial_entries'] = initial_list
        context['initial_data_json'] = json.dumps({
            'last_page': paginator.num_pages,
            'data': initial_list,
            'current_page': 1,
        }, default=str)
        context['entries'] = queryset
        return context


class CollectionEntryGridDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """AJAX endpoint for collection entry data"""
    permission_required = 'collections.view_collectionentry'

    def get(self, request):
        queryset = CollectionEntry.objects.select_related('sheet', 'member')
        
        if not request.user.is_superuser:
            if request.user.branch:
                queryset = queryset.filter(sheet__branch=request.user.branch)
            else:
                queryset = queryset.none()
        
        member_q = request.GET.get('member_name', '').strip()
        type_q = request.GET.get('collection_type', '').strip()
        
        if member_q:
            queryset = queryset.filter(member__name__icontains=member_q)
        if type_q:
            queryset = queryset.filter(collection_type=type_q)

        grid = TabulatorGrid(request.GET, queryset, search_fields=['member__name', 'collection_type'])
        resp = grid.get_response()
        
        for item in resp.get('data', []):
            entry = next((e for e in queryset if e.id == item['id']), None)
            if entry:
                item['member_name'] = entry.member.name
                item['collection_type'] = entry.get_collection_type_display()
                item['date'] = str(entry.sheet.date)
        
        resp['received_params'] = dict(request.GET)
        return JsonResponse(resp)


class CollectionEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new collection entry"""
    model = CollectionEntry
    form_class = CollectionEntryForm
    template_name = 'collections/entry_form.html'
    success_url = reverse_lazy('collections_entry_list')
    permission_required = 'collections.add_collectionentry'
