from rest_framework import serializers
from .models import (
    Product, ProductImage, PrintableArea, DesignPlacement, 
    Category, Attribute, AttributeValue, ProductVariant
)
from designs.models import Design 

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

# --- NEW IMAGE SERIALIZER ---

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'alt_text']

    def get_image_url(self, obj):
        if obj.image:
            url = obj.image.url
            
            # Add Cloudinary transformations for optimization
            # This works if you're using CloudinaryField
            if hasattr(obj.image, 'build_url'):
                url = obj.image.build_url(
                    quality='auto',           # Automatic quality adjustment
                    fetch_format='auto',      # Automatic format (WebP for supported browsers)
                    width=800,                # Resize to appropriate width
                    crop='limit',             # Don't upscale, only downscale
                    flags='progressive'       # Progressive JPEG loading
                )
            
            if url.startswith('http://'):
                url = 'https://' + url[7:]
            return url
        return None


# --- ATTRIBUTE SERIALIZERS ---

class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)

    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute_name', 'value']

class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'attributes', 'price_override', 'stock_quantity']

# --- PRODUCT SERIALIZERS ---

class PrintableAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintableArea
        fields = ['id', 'name', 'x', 'y', 'width', 'height']

class ProductSerializer(serializers.ModelSerializer):
    printable_areas = PrintableAreaSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    gallery = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 'image_url', 'gallery',
            'min_order_quantity', 'description', 'is_customizable', 
            'printable_areas', 'variants', 'category_name',
            'is_featured', 'is_trending', 'is_active'
        ]
        read_only_fields = ['id', 'is_trending', 'is_featured', 'is_active', 'is_customizable']

    def get_image_url(self, obj):
        if obj.image:
            url = obj.image.url
            
            # Add Cloudinary transformations for optimization
            # This works if you're using CloudinaryField
            if hasattr(obj.image, 'build_url'):
                url = obj.image.build_url(
                    quality='auto',           # Automatic quality adjustment
                    fetch_format='auto',      # Automatic format (WebP for supported browsers)
                    width=800,                # Resize to appropriate width
                    crop='limit',             # Don't upscale, only downscale
                    flags='progressive'       # Progressive JPEG loading
                )
            
            if url.startswith('http://'):
                url = 'https://' + url[7:]
            return url
        return None

    def get_category_name(self, obj):
        if obj.categories.exists():
            return obj.categories.first().name
        return None


class ProductListSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 'image_url', 
            'min_order_quantity', 'is_featured', 'is_customizable', 
            'is_trending', 'variants', 'category_name'
        ]

    def get_image_url(self, obj):
        if obj.image:
            url = obj.image.url
            
            # Add Cloudinary transformations for optimization
            # This works if you're using CloudinaryField
            if hasattr(obj.image, 'build_url'):
                url = obj.image.build_url(
                    quality='auto',           # Automatic quality adjustment
                    fetch_format='auto',      # Automatic format (WebP for supported browsers)
                    width=800,                # Resize to appropriate width
                    crop='limit',             # Don't upscale, only downscale
                    flags='progressive'       # Progressive JPEG loading
                )
            
            if url.startswith('http://'):
                url = 'https://' + url[7:]
            return url
        return None

    def get_category_name(self, obj):
        if obj.categories.exists():
            return obj.categories.first().name
        return None

class DesignPlacementSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_price = serializers.ReadOnlyField(source='product.base_price')
    
    design_name = serializers.ReadOnlyField(source='design.name')
    design_preview = serializers.ImageField(source='design.preview_image', read_only=True)
    product_image_url = serializers.SerializerMethodField()
    design_preview_url = serializers.SerializerMethodField()
    custom_text = serializers.ReadOnlyField(source='design.custom_text')
    overall_instructions = serializers.ReadOnlyField(source='design.overall_instructions')

    class Meta:
        model = DesignPlacement
        fields = [
            'id', 'design', 'product', 'printable_area', 
            'layout_data', 'preview_mockup',
            'product_name', 'product_image', 'product_price',
            'design_name', 'design_preview', 'custom_text', 'overall_instructions',
            'product_image_url', 'design_preview_url'
        ]

    def validate(self, data):
        product = data.get('product')
        printable_area = data.get('printable_area')

        if printable_area and product:
            if printable_area.product != product:
                raise serializers.ValidationError(
                    {"printable_area": "This area does not belong to the selected product."}
                )
        return data


    def get_product_image_url(self, obj):
        if obj.product.image:
            url = obj.product.image.url
            
            # Add Cloudinary transformations for optimization
            # This works if you're using CloudinaryField
            if hasattr(obj.product.image, 'build_url'):
                url = obj.product.image.build_url(
                    quality='auto',           # Automatic quality adjustment
                    fetch_format='auto',      # Automatic format (WebP for supported browsers)
                    width=800,                # Resize to appropriate width
                    crop='limit',             # Don't upscale, only downscale
                    flags='progressive'       # Progressive JPEG loading
                )
            
            if url.startswith('http://'):
                url = 'https://' + url[7:]
            return url
        return None


    def get_design_preview_url(self, obj):
        if obj.design.preview_image:
            url = obj.design.preview_image.url
            
            # Add Cloudinary transformations for optimization
            # This works if you're using CloudinaryField
            if hasattr(obj.design.preview_image, 'build_url'):
                url = obj.design.preview_image.build_url(
                    quality='auto',           # Automatic quality adjustment
                    fetch_format='auto',      # Automatic format (WebP for supported browsers)
                    width=800,                # Resize to appropriate width
                    crop='limit',             # Don't upscale, only downscale
                    flags='progressive'       # Progressive JPEG loading
                )
            
            if url.startswith('http://'):
                url = 'https://' + url[7:]
            return url
        return None