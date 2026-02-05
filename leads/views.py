from rest_framework import generics
from .models import Lead, InviteLink, GiftPreview
from .serializers import LeadSerializer, InviteLinkSerializer, GiftPreviewSerializer
from rest_framework.permissions import AllowAny

# LEAD VIEWS
class LeadListCreateView(generics.ListCreateAPIView):
    """
    List all leads (for admin) or create a new lead when they sign up.
    """
    queryset = Lead.objects.all().order_by('-created_at')
    serializer_class = LeadSerializer
    permission_classes = [AllowAny]  # Allow anyone to view/update their gift preview

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


# GIFT PREVIEW VIEWS
class GiftPreviewDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the specific gift (Mug, Frame, etc.) assigned to a lead.
    """
    queryset = GiftPreview.objects.all()
    serializer_class = GiftPreviewSerializer
    lookup_field = 'lead__id' # Allows looking up by the Lead's UUID