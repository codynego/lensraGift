from django.urls import path
from .views import (
    ResellerApplyView, 
    ResellerDashboardView, 
    CheckResellerStatusView
)

urlpatterns = [
    # Submit application
    path('apply/', ResellerApplyView.as_view(), name='reseller-apply'),
    # Get wallet balance and transactions
    path('dashboard/', ResellerDashboardView.as_view(), name='reseller-dashboard'),
    # Quick check for UI logic
    path('status/', CheckResellerStatusView.as_view(), name='reseller-status'),
]