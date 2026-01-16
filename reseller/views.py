from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ResellerProfile
from .serializers import (
    ResellerApplicationSerializer, 
    ResellerDashboardSerializer
)

class ResellerApplyView(generics.CreateAPIView):
    """Handles the initial reseller application."""
    serializer_class = ResellerApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Check if user already has an application
        if ResellerProfile.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "Application already submitted or profile exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().post(request, *args, **kwargs)

class ResellerDashboardView(generics.RetrieveAPIView):
    """Returns the wallet balance and transaction history for the logged-in user."""
    serializer_class = ResellerDashboardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Return the profile belonging to the authenticated user
        return get_object_or_404(ResellerProfile, user=self.request.user)

class CheckResellerStatusView(generics.GenericAPIView):
    """Lightweight check to see if a user is an approved reseller."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.reseller_profile
            return Response({
                "is_reseller": profile.status == 'APPROVED',
                "status": profile.status
            })
        except ResellerProfile.DoesNotExist:
            return Response({"is_reseller": False, "status": "NONE"})