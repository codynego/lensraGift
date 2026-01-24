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


from rest_framework import serializers
from .models import DigitalGift, AddOn, DigitalGiftAddOn, Occasion, ExperienceTier  # Assuming imports are needed

class DigitalGiftAddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalGiftAddOn
        fields = '__all__'  # Or specify fields if needed

class DigitalGiftSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField for writing and nested serializers for reading
    addons = DigitalGiftAddOnSerializer(many=True, read_only=True)
    addon_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
    use_ai_voice = serializers.BooleanField(write_only=True, required=False)
    shipping_address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    media_file = serializers.FileField(write_only=True, required=False)
    
    # We include these to show full names in the frontend rather than just IDs
    occasion_name = serializers.ReadOnlyField(source='occasion.name')
    tier_name = serializers.ReadOnlyField(source='tier.name')
    
    sender_name = serializers.CharField(required=True)
    sender_email = serializers.EmailField(required=True)
    recipient_name = serializers.CharField(required=True)
    recipient_email = serializers.EmailField(required=False, allow_blank=True)
    recipient_phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = DigitalGift
        fields = [
            'id','short_id', 'sender_name', 'sender_email', 'recipient_name', 
            'recipient_email', 'recipient_phone', 'occasion', 'occasion_name',
            'tier', 'tier_name', 'text_message', 'voice_message', 
            'video_message', 'scheduled_delivery', 'delivered', 
            'delivery_method', 'status', 'is_paid', 'addons', 'created_at',
            'use_ai_voice', 'shipping_address', 'addon_ids', 'session_id',
            'media_file'
        ]
        read_only_fields = ['id', 'status', 'is_paid', 'created_at', 'short_id']

    def create(self, validated_data):
        addon_ids = validated_data.pop('addon_ids', [])
        use_ai_voice = validated_data.pop('use_ai_voice', False)
        shipping_address = validated_data.pop('shipping_address', None)
        media_file = validated_data.pop('media_file', None)
        
        gift = DigitalGift.objects.create(**validated_data)
        
        if shipping_address:
            gift.shipping_address = shipping_address
        
        if media_file:
            if 'audio' in media_file.content_type:
                gift.voice_message = media_file
            elif 'video' in media_file.content_type:
                gift.video_message = media_file
            else:
                raise serializers.ValidationError("Invalid media file type. Only audio or video files are accepted.")
        
        gift.save()
        
        for addon_id in addon_ids:
            addon = AddOn.objects.get(id=addon_id)
            DigitalGiftAddOn.objects.create(gift=gift, addon=addon)
        
        # Handle AI voice generation if use_ai_voice is True
        # (Implement AI voice generation logic here if needed)
        
        return gift