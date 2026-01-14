from rest_framework import serializers
from .models import RewardProfile, RewardTransaction, RewardPerk

class PerkSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardPerk
        fields = ['id', 'title', 'description', 'point_cost', 'icon_name', 'is_active']

class RewardTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardTransaction
        fields = ['id', 'amount', 'description', 'transaction_type', 'coupon_code', 'is_used', 'created_at']
        read_only_fields = ['id', 'coupon_code', 'is_used', 'created_at']
        
class RewardProfileSerializer(serializers.ModelSerializer):
    # We include the transactions inside the profile for a single-page fetch
    transactions = RewardTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = RewardProfile
        fields = ['points', 'updated_at', 'transactions']