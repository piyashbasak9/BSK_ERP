from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.SettingsDashboardView.as_view(), name='settings_dashboard'),
    path('system/', views.SystemSettingsView.as_view(), name='system_settings'),
    path('audit/', views.AuditSettingsView.as_view(), name='audit_settings'),
    path('backup/', views.BackupRestoreView.as_view(), name='backup_restore'),

    # User Management
    path('users/', views.UserListView.as_view(), name='user_management'),
    path('users/add/', views.UserCreateView.as_view(), name='user_add'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # Branch Management
    path('branches/', views.BranchListView.as_view(), name='branch_management'),
    path('branches/add/', views.BranchCreateView.as_view(), name='branch_add'),
    path('branches/<int:pk>/edit/', views.BranchUpdateView.as_view(), name='branch_edit'),
    path('branches/<int:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),
]