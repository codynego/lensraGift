from django.urls import path
from . import views

urlpatterns = [
    # Get balance and history
    path('dashboard/', views.RewardDashboardView.as_view(), name='reward-dashboard'),
    
    # Get all perks
    path('perks/', views.AvailablePerksView.as_view(), name='reward-perks'),
    
    # Redeem a specific perk
    path('redeem/<int:perk_id>/', views.RedeemPerkView.as_view(), name='redeem-perk'),
]