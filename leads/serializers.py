from rest_framework import serializers
from .models import Lead, InviteLink, GiftPreview, WhatsAppLog

class InviteLinkSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False)

    class Meta:
        model = InviteLink
        fields = ['code', 'owner', 'clicks', 'created_at']
        read_only_fields = ['clicks', 'created_at']

    def create(self, validated_data):
        if 'code' not in validated_data or not validated_data['code']:
            validated_data['code'] = self.generate_unique_code()
        return super().create(validated_data)

    def generate_unique_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not InviteLink.objects.filter(code=code).exists():
                return code


class GiftPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftPreview
        fields = ['lead', 'preview_type', 'blurred_image', 'created_at']


class WhatsAppLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppLog
        fields = ['lead', 'message_type', 'sent_at']


from rest_framework import serializers, status


class LeadSerializer(serializers.ModelSerializer):
    gift_preview = GiftPreviewSerializer(read_only=True, source='giftpreview')
    invite_links = InviteLinkSerializer(many=True, read_only=True, source='invitelink_set')
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
        # Remove unique validator from WhatsApp here so we can handle it manually in create()
        extra_kwargs = {
            'whatsapp': {'validators': []} 
        }

    def to_internal_value(self, data):
        """
        Convert the 'invited_by' string code into the Lead ID 
        before validation kicks in.
        """
        if 'invited_by' in data and isinstance(data['invited_by'], str):
            try:
                invite = InviteLink.objects.get(code=data['invited_by'])
                data['invited_by'] = invite.owner.id
                # Store the invite object for potential click increment in create()
                self._invite = invite
            except InviteLink.DoesNotExist:
                raise serializers.ValidationError({
                    "invited_by": "Invalid invite code."
                })
        return super().to_internal_value(data)

    def create(self, validated_data):
        """
        Handle 'Get or Create' logic for WhatsApp numbers.
        """
        whatsapp = validated_data.get('whatsapp')
        
        # Check if the lead already exists
        instance = Lead.objects.filter(whatsapp=whatsapp).first()
        
        increment_clicks = False
        
        if instance:
            # Update existing lead with any new info (like name or email)
            for attr, value in validated_data.items():
                if attr == 'invited_by':
                    if instance.invited_by:
                        # Do not overwrite existing invited_by
                        continue
                    else:
                        # Set it if not already set
                        setattr(instance, attr, value)
                        increment_clicks = True
                else:
                    setattr(instance, attr, value)
            instance.save()
        else:
            # If it doesn't exist, create a new one
            instance = Lead.objects.create(**validated_data)
            if 'invited_by' in validated_data:
                increment_clicks = True
        
        # Increment clicks only if we set invited_by
        if increment_clicks and hasattr(self, '_invite'):
            self._invite.clicks += 1
            self._invite.save()
        
        return instance