from django.urls import path
from .views import DesignListCreateView, DesignDetailView, FeaturedDesignListView

app_name = 'designs'

urlpatterns = [
    path('', DesignListCreateView.as_view(), name='design-list-create'),
    path('<int:pk>/', DesignDetailView.as_view(), name='design-detail'),
    path("featured/", FeaturedDesignListView.as_view(), name="featured-designs"),
]
