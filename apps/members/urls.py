from django.urls import path
from . import views

urlpatterns = [
    path('', views.MemberListView.as_view(), name='member_list'),
    path('data/', views.MemberGridDataView.as_view(), name='member_data'),
    path('add/', views.MemberCreateView.as_view(), name='member_add'),
    path('<int:pk>/edit/', views.MemberUpdateView.as_view(), name='member_edit'),
    path('<int:pk>/delete/', views.MemberDeleteView.as_view(), name='member_delete'),
    path('<int:pk>/json/', views.MemberDetailJsonView.as_view(), name='member_detail_json'),
    path('<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
]