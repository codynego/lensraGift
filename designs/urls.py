from django.urls import path
from .views import DesignListCreateView, DesignDetailView, PublicDesignsView

app_name = 'designs'

urlpatterns = [
    # api/designs/
    path('', DesignListCreateView.as_view(), name='design-list-create'),
    # api/designs/5/
    path('<int:pk>/', DesignDetailView.as_view(), name='design-detail'),
    path('public/', PublicDesignsView.as_view(), name='public-designs'),
]