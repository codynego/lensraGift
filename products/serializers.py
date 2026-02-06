from rest_framework import serializers
from .models import (
    Product, ProductImage, PrintableArea, DesignPlacement, 
    Category, Attribute, AttributeValue, ProductVariant, Tag
)
from designs.models import Design 



class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name', 'slug']

class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)  # Simple parent ID
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)  # Optional: Parent name
    subcategories = serializers.SerializerMethodField()  # For nested subcats (limited depth)
    full_path = serializers.SerializerMethodField()  # Computed full category path
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent_id', 'parent_name', 'subcategories', 'full_path', 'image_url']

    def get_subcategories(self, obj):
        # Recursively serialize subcategories, but limit depth to avoid infinite loops
        # Use context to track depth if needed (e.g., pass {'depth': 1} in view)
        depth = self.context.get('depth', 0)
        if depth > 2:  # Arbitrary max depth to prevent deep nesting
            return []
        subcategory_qs = obj.subcategories.all()
        return CategorySerializer(subcategory_qs, many=True, context={'depth': depth + 1}).data
    
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

    def get_full_path(self, obj):
        # Build a breadcrumb-style path: "Grandparent > Parent > Name"
        path = []
        current = obj
        while current:
            path.append(current.name)
            current = current.parent
        return ' > '.join(reversed(path)) if path else obj.name

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
    categories = CategorySerializer(many=True, read_only=True)  # Optional: Full category details
    category_path = serializers.SerializerMethodField()  # Replaces category_name
    image_url = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 'image_url', 'gallery',
            'min_order_quantity', 'description', 'is_customizable', 
            'printable_areas', 'variants', 'tags',
            'is_featured', 'is_trending', 'is_active', 'categories', 'category_path', 'message',
        ]
        read_only_fields = ['id', 'is_trending', 'is_featured', 'is_active', 'is_customizable', 'tags', 'message']

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

    def get_category_path(self, obj):
        if obj.categories.exists():
            primary_cat = obj.categories.first()
            return CategorySerializer(primary_cat).data.get('full_path')  # Use the new full_path
        return None



class ProductListSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)  # Optional: Full category details
    category_path = serializers.SerializerMethodField()  # Replaces category_name
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 'image_url', 
            'min_order_quantity', 'is_featured', 'is_customizable', 
            'is_trending', 'variants', 'categories', 'category_path', 'tags', 'message',
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

    def get_category_path(self, obj):
        if obj.categories.exists():
            primary_cat = obj.categories.first()
            return CategorySerializer(primary_cat).data.get('full_path')  # Use the new full_path
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