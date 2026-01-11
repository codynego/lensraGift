from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Design
from .serializers import DesignSerializer, DesignCreateSerializer
from rest_framework.permissions import AllowAny


class FeaturedDesignListView(generics.ListAPIView):
    """
    View for listing featured designs.
    Used on homepage / discovery pages.
    """

    serializer_class = DesignSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Design.objects.filter(is_featured=True).order_by('-created_at')


class DesignListCreateView(generics.ListCreateAPIView):
    """View for listing and creating designs."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DesignCreateSerializer
        return DesignSerializer

    def get_queryset(self):
        return Design.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DesignDetailView(generics.RetrieveDestroyAPIView):
    """View for retrieving and deleting a design."""

    serializer_class = DesignSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Design.objects.filter(user=self.request.user)
