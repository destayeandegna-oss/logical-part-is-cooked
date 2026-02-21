from django.urls import path
from .views import (
    LeaveRequestListView, LeaveRequestDetailView,
    LeaveApprovalView, LeaveBalanceView
)

urlpatterns = [
    path('requests/', LeaveRequestListView.as_view(), name='leave-request-list'),
    path('requests/<int:pk>/', LeaveRequestDetailView.as_view(), name='leave-request-detail'),
    path('requests/<int:pk>/approve/', LeaveApprovalView.as_view(), name='leave-request-approve'),
    path('balance/', LeaveBalanceView.as_view(), name='leave-balance'),
]