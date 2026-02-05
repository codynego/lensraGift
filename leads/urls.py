from django.urls import path
from . import views

urlpatterns = [
    # Lead Endpoints
    path('', views.LeadListCreateView.as_view(), name='lead-list-create'),
    path('<uuid:id>/', views.LeadDetailView.as_view(), name='lead-detail'),

    # Referral Endpoints
    path('invites/', views.InviteLinkListCreateView.as_view(), name='invite-list'),

    # Gift Preview Endpoints
    path('previews/<uuid:lead__id>/', views.GiftPreviewDetailView.as_view(), name='preview-detail'),
]