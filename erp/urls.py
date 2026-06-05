from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from apps.authentication.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('branches/', include('apps.branches.urls')),
    path('members/', include('apps.members.urls')),
    path('savings/', include('apps.savings.urls')),
    path('loans/', include('apps.loans.urls')),
    path('collections/', include('apps.collections.urls')),
    path('accounting/', include('apps.accounting.urls')),
    path('reports/', include('apps.reports.urls')),
    path('audit/', include('apps.audit.urls')),
    path('settings/', include('apps.settings.urls')),
]