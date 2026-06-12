import json
import csv
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import AuditLog
from .forms import AuditLogFilterForm
from erp.utils.tabulator import TabulatorGrid


class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser
    def handle_no_permission(self):
        from django.contrib import messages
        messages.error(self.request, 'You do not have permission to view audit logs.')
        return super().handle_no_permission()


class AuditLogListView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'audit/log_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['columns'] = [
            {"title": "Timestamp", "field": "timestamp", "width": 150},
            {"title": "User", "field": "user", "sorter": "string", "width": 120},
            {"title": "Action", "field": "action", "width": 100},
            {"title": "Resource", "field": "resource", "sorter": "string", "widthGrow": 1},
            {"title": "IP Address", "field": "ip_address", "width": 120},
        ]
        context['columns_json'] = json.dumps(context['columns'])
        context['filter_form'] = AuditLogFilterForm(self.request.GET)
        return context


class AuditLogGridDataView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def get(self, request):
        queryset = self.get_filtered_queryset(request)
        grid = TabulatorGrid(request.GET, queryset, search_fields=['username', 'resource'])
        resp = grid.get_response()
        for item in resp.get('data', []):
            item['timestamp'] = item['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if item.get('timestamp') else ''
        return JsonResponse(resp)

    def get_filtered_queryset(self, request):
        qs = AuditLog.objects.all()
        form = AuditLogFilterForm(request.GET)
        if form.is_valid():
            log_types = form.cleaned_data.get('log_type')
            if log_types:
                qs = qs.filter(action__in=log_types)
            username = form.cleaned_data.get('user')
            if username:
                qs = qs.filter(username__icontains=username)
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            if start_date:
                qs = qs.filter(timestamp__date__gte=start_date)
            if end_date:
                qs = qs.filter(timestamp__date__lte=end_date)
        return qs


class AuditLogDetailView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def get(self, request, log_id):
        try:
            log = AuditLog.objects.get(pk=log_id)
            return JsonResponse({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'user': log.username,
                'action': log.action,
                'resource': log.resource,
                'resource_id': log.resource_id,
                'old_values': log.old_values,
                'new_values': log.new_values,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
            })
        except AuditLog.DoesNotExist:
            return JsonResponse({'error': 'Log not found'}, status=404)


class AuditLogExportView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def get(self, request):
        qs = AuditLogGridDataView().get_filtered_queryset(request)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'User', 'Action', 'Resource', 'Resource ID', 'IP Address', 'Old Values', 'New Values'])
        for log in qs.iterator():
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.username,
                log.action,
                log.resource,
                log.resource_id,
                log.ip_address,
                json.dumps(log.old_values),
                json.dumps(log.new_values),
            ])
        return response


class SystemActivityDashboardView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'audit/activity_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        today_end = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

        context['today_logins'] = AuditLog.objects.filter(action='login', timestamp__range=(today_start, today_end)).count()
        context['today_data_changes'] = AuditLog.objects.filter(action__in=['create', 'update'], timestamp__range=(today_start, today_end)).count()
        context['today_deletions'] = AuditLog.objects.filter(action='delete', timestamp__range=(today_start, today_end)).count()
        context['active_sessions'] = 0  # would require session tracking, optional

        # Chart data: last 7 days activity counts
        last_7_days = []
        for i in range(6, -1, -1):
            day = today - timezone.timedelta(days=i)
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
            day_end = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.max.time()))
            count = AuditLog.objects.filter(timestamp__range=(day_start, day_end)).count()
            last_7_days.append({'date': day.strftime('%Y-%m-%d'), 'count': count})
        context['chart_data'] = json.dumps(last_7_days)

        # Recent activities
        context['recent_activities'] = AuditLog.objects.order_by('-timestamp')[:20].values('timestamp', 'username', 'action', 'resource', 'resource_id')
        return context