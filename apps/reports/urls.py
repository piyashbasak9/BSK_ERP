from django.urls import path
from . import views

urlpatterns = [
    path('', views.ReportListView.as_view(), name='report_list'),
    path('member-summary/', views.MemberSummaryReportView.as_view(), name='report_member_summary'),
    path('loan-summary/', views.LoanSummaryReportView.as_view(), name='report_loan_summary'),
    path('savings-summary/', views.SavingsSummaryReportView.as_view(), name='report_savings_summary'),
    path('collection-summary/', views.CollectionSummaryReportView.as_view(), name='report_collection_summary'),
    path('account-balance/', views.AccountBalanceReportView.as_view(), name='report_account_balance'),
    path('export/<str:report_type>/', views.ReportExportView.as_view(), name='report_export'),
]
