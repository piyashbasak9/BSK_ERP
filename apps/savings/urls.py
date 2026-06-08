from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.SavingsDashboardView.as_view(), name='savings_dashboard'),

    # Savings Products
    path('products/', views.SavingsProductListView.as_view(), name='savings_product_list'),
    path('products/data/', views.SavingsProductGridDataView.as_view(), name='savings_product_data'),
    path('products/add/', views.SavingsProductCreateView.as_view(), name='savings_product_add'),
    path('products/<int:pk>/edit/', views.SavingsProductUpdateView.as_view(), name='savings_product_edit'),
    path('products/<int:pk>/delete/', views.SavingsProductDeleteView.as_view(), name='savings_product_delete'),
    path('products/<int:pk>/json/', views.SavingsProductDetailJsonView.as_view(), name='savings_product_detail_json'),

    # Savings Accounts
    path('accounts/', views.SavingsAccountListView.as_view(), name='savings_account_list'),
    path('accounts/data/', views.SavingsAccountGridDataView.as_view(), name='savings_account_data'),
    path('accounts/add/', views.SavingsAccountCreateView.as_view(), name='savings_account_add'),
    path('accounts/<int:pk>/edit/', views.SavingsAccountUpdateView.as_view(), name='savings_account_edit'),
    path('accounts/<int:pk>/delete/', views.SavingsAccountDeleteView.as_view(), name='savings_account_delete'),
    path('accounts/<int:pk>/json/', views.SavingsAccountDetailJsonView.as_view(), name='savings_account_detail_json'),
    path('accounts/<int:pk>/statement/', views.SavingsStatementView.as_view(), name='savings_account_statement'),

    # Savings Transactions
    path('transactions/', views.SavingsTransactionListView.as_view(), name='savings_transaction_list'),
    path('transactions/data/', views.SavingsTransactionGridDataView.as_view(), name='savings_transaction_data'),
    path('transactions/add/', views.SavingsTransactionCreateView.as_view(), name='savings_transaction_add'),
    path('transactions/<int:pk>/reverse/', views.SavingsTransactionReverseView.as_view(), name='savings_transaction_reverse'),
]