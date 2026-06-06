from django.urls import path
from . import views

urlpatterns = [
    path('', views.BranchListView.as_view(), name='branch_list'),
    path('data/', views.BranchGridDataView.as_view(), name='branch_data'),
    path('add/', views.BranchCreateView.as_view(), name='branch_add'),
    path('<int:pk>/edit/', views.BranchUpdateView.as_view(), name='branch_edit'),
    path('<int:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),
    path('<int:pk>/json/', views.BranchDetailJsonView.as_view(), name='branch_detail_json'),
    path('<int:pk>/', views.BranchDetailView.as_view(), name='branch_detail'),
]
