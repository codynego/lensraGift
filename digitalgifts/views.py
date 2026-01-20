from rest_framework import generics
from .models import Occasion, ExperienceTier, DigitalGift, AddOn, DigitalGiftAddOn
from .serializers import (
    OccasionSerializer, 
    ExperienceTierSerializer, 
    AddOnSerializer, 
    DigitalGiftSerializer
)

# 1. Fetch Occasions for Step 1
class OccasionListView(generics.ListAPIView):
    queryset = Occasion.objects.all()
    serializer_class = OccasionSerializer

# 2. Fetch Tiers for Step 2
class ExperienceTierListView(generics.ListAPIView):
    queryset = ExperienceTier.objects.all()
    serializer_class = ExperienceTierSerializer

# 3. Fetch Add-Ons for Step 3
class AddOnListView(generics.ListAPIView):
    queryset = AddOn.objects.all()
    serializer_class = AddOnSerializer

# 4. Handle Gift Creation & Final Submission
class DigitalGiftListCreateView(generics.ListCreateAPIView):
    queryset = DigitalGift.objects.all()
    serializer_class = DigitalGiftSerializer

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
    lookup_field = 'id'