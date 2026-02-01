from rest_framework import serializers
from .models import ResellerProfile, WalletTransaction
from core.tasks.reseller import send_reseller_application_email

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'description', 'timestamp', 'order']

class ResellerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResellerProfile
        fields = ['whatsapp_number', 'marketing_plan', 'business_name']

    def create(self, validated_data):
        user = self.context['request'].user
        reseller = ResellerProfile.objects.create(user=user, **validated_data)

        # Trigger async email
        send_reseller_application_email.delay(reseller.id)

        return reseller

class ResellerDashboardSerializer(serializers.ModelSerializer):
    # This nesting allows the frontend to get profile + transactions in one call
    transactions = WalletTransactionSerializer(many=True, read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ResellerProfile
        fields = ['email', 'status', 'wallet_balance', 'business_name', 'applied_at', 'transactions']