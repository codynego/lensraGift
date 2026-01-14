from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import RewardProfile, RewardPerk, RewardTransaction
from .serializers import RewardProfileSerializer, PerkSerializer
import secrets
import string
from django.db import transaction # Essential for point safety

class RewardDashboardView(generics.RetrieveAPIView):
    """Returns user points and history"""
    permission_classes = [IsAuthenticated]
    serializer_class = RewardProfileSerializer

    def get_object(self):
        return self.request.user.reward_profile

class AvailablePerksView(generics.ListAPIView):
    """Returns list of active perks"""
    queryset = RewardPerk.objects.filter(is_active=True)
    serializer_class = PerkSerializer

class RedeemPerkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, perk_id):
        try:
            # We use select_for_update() to prevent race conditions 
            # (e.g., clicking twice really fast before the first save finishes)
            with transaction.atomic():
                perk = RewardPerk.objects.get(id=perk_id, is_active=True)
                profile = request.user.reward_profile

                if profile.points < perk.point_cost:
                    return Response(
                        {"error": "Insufficient points balance"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 1. Deduct Points
                profile.points -= perk.point_cost
                profile.save()

                # 2. Generate a readable unique coupon code
                # Example: RW-A1B2-C3D4
                random_string = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                generated_code = f"RW-{random_string[:4]}-{random_string[4:]}"

                # 3. Log Transaction with the new fields
                new_tx = RewardTransaction.objects.create(
                    profile=profile,
                    amount=-perk.point_cost,
                    description=f"Redeemed: {perk.title}",
                    transaction_type='redeemed',
                    coupon_code=generated_code,
                    is_used=False
                )

                return Response({
                    "message": "Perk redeemed successfully",
                    "new_balance": profile.points,
                    "coupon_code": generated_code # Send it back for instant UI update if needed
                }, status=status.HTTP_200_OK)

        except RewardPerk.DoesNotExist:
            return Response({"error": "Perk not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)