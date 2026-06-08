from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='loans_product_list', permanent=False), name='loans_index'),

    # Loan Products
    path('products/', views.LoanProductListView.as_view(), name='loans_product_list'),
    path('products/data/', views.LoanProductGridDataView.as_view(), name='loans_product_data'),
    path('products/add/', views.LoanProductCreateView.as_view(), name='loans_product_add'),
    path('products/<int:pk>/edit/', views.LoanProductUpdateView.as_view(), name='loans_product_edit'),
    path('products/<int:pk>/delete/', views.LoanProductDeleteView.as_view(), name='loans_product_delete'),
    path('products/<int:pk>/json/', views.LoanProductDetailJsonView.as_view(), name='loans_product_detail_json'),

    # Loan Applications
    path('applications/', views.LoanApplicationListView.as_view(), name='loans_application_list'),
    path('applications/data/', views.LoanApplicationGridDataView.as_view(), name='loans_application_data'),
    path('applications/add/', views.LoanApplicationCreateView.as_view(), name='loans_application_add'),
    path('applications/<int:pk>/edit/', views.LoanApplicationUpdateView.as_view(), name='loans_application_edit'),
    path('applications/<int:pk>/delete/', views.LoanApplicationDeleteView.as_view(), name='loans_application_delete'),
    path('applications/<int:pk>/json/', views.LoanApplicationDetailJsonView.as_view(), name='loans_application_detail_json'),

    # Loan Disbursements
    path('disbursements/', views.LoanDisbursementListView.as_view(), name='loans_disbursement_list'),
    path('disbursements/data/', views.LoanDisbursementGridDataView.as_view(), name='loans_disbursement_data'),
    path('disbursements/add/', views.LoanDisbursementCreateView.as_view(), name='loans_disbursement_add'),
    path('disbursements/<int:pk>/edit/', views.LoanDisbursementEditView.as_view(), name='loans_disbursement_edit'),

    # Loan Installment Schedules
    path('schedules/', views.LoanInstallmentScheduleListView.as_view(), name='loans_schedule_list'),
    path('schedules/data/', views.LoanInstallmentScheduleGridDataView.as_view(), name='loans_schedule_data'),
    path('schedules/<int:pk>/edit/', views.LoanInstallmentScheduleUpdateView.as_view(), name='loans_schedule_edit'),
    path('schedules/<int:pk>/pay/', views.LoanPaymentView.as_view(), name='loans_schedule_pay'),
]