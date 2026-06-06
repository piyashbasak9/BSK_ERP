from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
    path('logs/data/', views.AuditLogGridDataView.as_view(), name='audit_log_data'),
    path('logs/<int:log_id>/', views.AuditLogDetailView.as_view(), name='audit_log_detail'),
    path('logs/export/', views.AuditLogExportView.as_view(), name='audit_log_export'),
    path('activity/', views.SystemActivityDashboardView.as_view(), name='audit_activity_dashboard'),
]
