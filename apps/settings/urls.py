from django.urls import path
from . import views

urlpatterns = [
    path('', views.SettingsDashboardView.as_view(), name='settings_dashboard'),
    path('system/', views.SystemSettingsView.as_view(), name='system_settings'),
    path('users/', views.UserManagementView.as_view(), name='user_management'),
    path('branches/', views.BranchManagementView.as_view(), name='branch_management'),
    path('backup/', views.BackupRestoreView.as_view(), name='backup_restore'),
    path('audit/', views.AuditSettingsView.as_view(), name='audit_settings'),
]
