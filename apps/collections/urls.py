from django.urls import path
from . import views

urlpatterns = [
    # Daily Collection Sheets
    path('sheets/', views.DailyCollectionSheetListView.as_view(), name='collections_sheet_list'),
    path('sheets/data/', views.DailyCollectionSheetGridDataView.as_view(), name='collections_sheet_data'),
    path('sheets/add/', views.DailyCollectionSheetCreateView.as_view(), name='collections_sheet_add'),
    path('sheets/<int:pk>/edit/', views.DailyCollectionSheetUpdateView.as_view(), name='collections_sheet_edit'),
    path('sheets/<int:pk>/json/', views.DailyCollectionSheetDetailJsonView.as_view(), name='collections_sheet_detail_json'),
    
    # Collection Entries
    path('entries/', views.CollectionEntryListView.as_view(), name='collections_entry_list'),
    path('entries/data/', views.CollectionEntryGridDataView.as_view(), name='collections_entry_data'),
    path('entries/add/', views.CollectionEntryCreateView.as_view(), name='collections_entry_add'),
]
