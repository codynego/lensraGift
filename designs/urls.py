from django.urls import path
from .views import DesignListCreateView, DesignDetailView

app_name = 'designs'

urlpatterns = [
    path('', DesignListCreateView.as_view(), name='design-list-create'),
    path('<int:pk>/', DesignDetailView.as_view(), name='design-detail'),
]
