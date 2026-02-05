from rest_framework import serializers
from .models import Lead, InviteLink, GiftPreview, WhatsAppLog

class InviteLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteLink
        fields = ['code', 'owner', 'clicks', 'created_at']
        read_only_fields = ['clicks', 'created_at']


class GiftPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftPreview
        fields = ['lead', 'preview_type', 'blurred_image', 'created_at']


class WhatsAppLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppLog
        fields = ['lead', 'message_type', 'sent_at']


class LeadSerializer(serializers.ModelSerializer):
    # Optional: Nesting the preview and invite link for a complete Lead profile
    gift_preview = GiftPreviewSerializer(read_only=True, source='giftpreview')
    invite_links = InviteLinkSerializer(many=True, read_only=True, source='invitelink_set')
    
    # Show the count of people they've referred
    referral_count = serializers.IntegerField(source='referrals.count', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'whatsapp', 'email', 'name', 
            'invited_by', 'has_viewed_preview', 
            'has_shared', 'created_at', 
            'referral_count', 'gift_preview', 'invite_links'
        ]
        read_only_fields = ['id', 'created_at']