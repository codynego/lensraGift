from django.urls import path
from . import views

urlpatterns = [
    # Configuration Endpoints (Wizard Steps 1-3)
    path('occasions/', views.OccasionListView.as_view(), name='occasion-list'),
    path('tiers/', views.ExperienceTierListView.as_view(), name='tier-list'),
    path('addons/', views.AddOnListView.as_view(), name='addon-list'),

    # Gift Creation & Management
    path('gifts/', views.DigitalGiftListCreateView.as_view(), name='gift-create'),
    path('gifts/<str:short_id>/', views.DigitalGiftDetailView.as_view(), name='gift-detail'),
]