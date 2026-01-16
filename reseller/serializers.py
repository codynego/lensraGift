from rest_framework import serializers
from .models import ResellerProfile, WalletTransaction

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'description', 'timestamp', 'order']

class ResellerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResellerProfile
        fields = ['whatsapp_number', 'marketing_plan', 'business_name']

    def create(self, validated_data):
        # The user is injected from the view context
        user = self.context['request'].user
        return ResellerProfile.objects.create(user=user, **validated_data)

class ResellerDashboardSerializer(serializers.ModelSerializer):
    # This nesting allows the frontend to get profile + transactions in one call
    transactions = WalletTransactionSerializer(many=True, read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ResellerProfile
        fields = ['email', 'status', 'wallet_balance', 'business_name', 'applied_at', 'transactions']