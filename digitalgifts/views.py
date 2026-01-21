from rest_framework import generics
from .models import Occasion, ExperienceTier, DigitalGift, AddOn, DigitalGiftAddOn
from .serializers import (
    OccasionSerializer, 
    ExperienceTierSerializer, 
    AddOnSerializer, 
    DigitalGiftSerializer
)
from rest_framework.permissions import AllowAny

# 1. Fetch Occasions for Step 1
class OccasionListView(generics.ListAPIView):
    queryset = Occasion.objects.all()
    serializer_class = OccasionSerializer
    permission_classes = [AllowAny]

# 2. Fetch Tiers for Step 2
class ExperienceTierListView(generics.ListAPIView):
    queryset = ExperienceTier.objects.all()
    serializer_class = ExperienceTierSerializer
    permission_classes = [AllowAny]

# 3. Fetch Add-Ons for Step 3
class AddOnListView(generics.ListAPIView):
    queryset = AddOn.objects.all()
    serializer_class = AddOnSerializer
    permission_classes = [AllowAny]
# 4. Handle Gift Creation & Final Submission
class DigitalGiftListCreateView(generics.ListCreateAPIView):
    queryset = DigitalGift.objects.all()
    serializer_class = DigitalGiftSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Save the main gift instance
        gift = serializer.save()
        
        # Extract selected_addons from the request (e.g., [1, 3])
        # This allows the frontend to send IDs in a single POST
        addon_ids = self.request.data.get('selected_addons', [])
        
        if addon_ids:
            addons_to_create = [
                DigitalGiftAddOn(gift=gift, addon_id=aid) for aid in addon_ids
            ]
            DigitalGiftAddOn.objects.bulk_create(addons_to_create)

# 5. Detail view for the "Success Page" or "Tracking"

class DigitalGiftDetailView(generics.RetrieveAPIView):
    queryset = DigitalGift.objects.all()
    serializer_class = DigitalGiftSerializer
    permission_classes = [AllowAny]
    lookup_field = 'short_id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Mark as opened only once
        if not instance.is_opened:
            instance.is_opened = True
            instance.open_count += 1
            instance.opened_at = timezone.now()
            instance.save(update_fields=["is_opened", "open_count", "opened_at"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
