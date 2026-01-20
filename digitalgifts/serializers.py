from rest_framework import serializers
from .models import Occasion, ExperienceTier, DigitalGift, AddOn, DigitalGiftAddOn

class OccasionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occasion
        fields = ['id', 'name', 'description', 'slug']


class ExperienceTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienceTier
        fields = ['id', 'name', 'description', 'price', 'recommended']


class AddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOn
        fields = ['id', 'name', 'description', 'price']


class DigitalGiftAddOnSerializer(serializers.ModelSerializer):
    # This nested serializer allows us to see the AddOn details inside the Gift
    addon_details = AddOnSerializer(source='addon', read_only=True)

    class Meta:
        model = DigitalGiftAddOn
        fields = ['id', 'addon', 'addon_details']


class DigitalGiftSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField for writing and nested serializers for reading
    addons = DigitalGiftAddOnSerializer(many=True, read_only=True)
    addon_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
    use_ai_voice = serializers.BooleanField(write_only=True, required=False)
    shipping_address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # We include these to show full names in the frontend rather than just IDs
    occasion_name = serializers.ReadOnlyField(source='occasion.name')
    tier_name = serializers.ReadOnlyField(source='tier.name')

    class Meta:
        model = DigitalGift
        fields = [
            'id', 'sender_name', 'sender_email', 'recipient_name', 
            'recipient_email', 'recipient_phone', 'occasion', 'occasion_name',
            'tier', 'tier_name', 'text_message', 'voice_message', 
            'video_message', 'scheduled_delivery', 'delivered', 
            'delivery_method', 'status', 'is_paid', 'addons', 'created_at',
            'use_ai_voice', 'shipping_address', 'addon_ids'
        ]
        read_only_fields = ['id', 'status', 'is_paid', 'created_at']

    def create(self, validated_data):
        addon_ids = validated_data.pop('addon_ids', [])
        use_ai_voice = validated_data.pop('use_ai_voice', False)
        shipping_address = validated_data.pop('shipping_address', None)
        
        gift = DigitalGift.objects.create(**validated_data)
        
        if shipping_address:
            gift.shipping_address = shipping_address
            gift.save()
        
        for addon_id in addon_ids:
            addon = AddOn.objects.get(id=addon_id)
            DigitalGiftAddOn.objects.create(gift=gift, addon=addon)
        
        # Handle AI voice generation if use_ai_voice is True
        # (Implement AI voice generation logic here if needed)
        
        return gift