from django.urls import path
from . import views

urlpatterns = [
    # Accounts
    path('accounts/', views.AccountListView.as_view(), name='account_list'),
    path('accounts/data/', views.AccountGridDataView.as_view(), name='account_data'),
    path('accounts/add/', views.AccountCreateView.as_view(), name='account_add'),
    path('accounts/<int:pk>/edit/', views.AccountUpdateView.as_view(), name='account_edit'),
    path('accounts/<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),
    path('accounts/<int:pk>/json/', views.AccountDetailJsonView.as_view(), name='account_detail_json'),
    
    # Journal Entries
    path('entries/', views.JournalEntryListView.as_view(), name='journalentry_list'),
    path('entries/data/', views.JournalEntryGridDataView.as_view(), name='journalentry_data'),
    path('entries/add/', views.JournalEntryCreateView.as_view(), name='journalentry_add'),
    path('entries/<int:pk>/edit/', views.JournalEntryUpdateView.as_view(), name='journalentry_edit'),
    path('entries/<int:pk>/delete/', views.JournalEntryDeleteView.as_view(), name='journalentry_delete'),
    path('entries/<int:pk>/json/', views.JournalEntryDetailJsonView.as_view(), name='journalentry_detail_json'),
]
