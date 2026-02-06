from rest_framework import generics
from .models import Lead, InviteLink, GiftPreview
from .serializers import LeadSerializer, InviteLinkSerializer, GiftPreviewSerializer
from rest_framework.permissions import AllowAny

# LEAD VIEWS
class LeadListCreateView(generics.ListCreateAPIView):
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # This will now either create a new Lead or update the existing one
        instance = serializer.save() 
        
        # Check if it was an update or a create to return the right status code
        status_code = status.HTTP_201_CREATED # Default
        
        return Response(serializer.data, status=status_code)

class LeadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (e.g., mark has_shared=True), or delete a lead.
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    lookup_field = 'id'


# INVITE LINK VIEWS
class InviteLinkListCreateView(generics.ListCreateAPIView):
    queryset = InviteLink.objects.all()
    serializer_class = InviteLinkSerializer
    permission_classes = [AllowAny] 

# GIFT PREVIEW VIEWS
class GiftPreviewDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the specific gift (Mug, Frame, etc.) assigned to a lead.
    """
    queryset = GiftPreview.objects.all()
    serializer_class = GiftPreviewSerializer
    lookup_field = 'lead__id' # Allows looking up by the Lead's UUID



import random
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from products.models import Product
from products.serializers import ProductSerializer
from django.db import models


class RandomProductRecommendationAPIView(GenericAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True,
            is_customizable=True
        )

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"detail": "No products available"},
                status=404
            )

        # Bias towards featured / trending
        featured = queryset.filter(is_featured=True)
        if featured.exists():
            product = random.choice(featured)
        else:
            product = random.choice(queryset)

        serializer = self.get_serializer(product)

        # Optional: increment preview count
        Product.objects.filter(pk=product.pk).update(
            view_count=models.F("view_count") + 1
        )

        return Response(serializer.data)
