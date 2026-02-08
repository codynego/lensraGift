from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from designs.models import Design
from cloudinary.models import CloudinaryField
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True) # e.g., 'for-her'

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = CloudinaryField(
        "category_image",
        blank=True,
        null=True
    )
    slug = models.SlugField(unique=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    class Meta:
        verbose_name_plural = "Categories"

    def get_full_path(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])

    def __str__(self):
        return self.get_full_path()
    
    def __str__(self): 
        return self.name  

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)]
    )
    categories = models.ManyToManyField(
        Category, 
        related_name="products",
        blank=True
    )
    image = CloudinaryField(
        "product_image",
        blank=True,
        null=True
    )
    min_order_quantity = models.PositiveIntegerField(default=1, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    product_design = CloudinaryField(
        "product_design_image",
        blank=True,
        null=True
    )
    tags = models.ManyToManyField(Tag, related_name="products", blank=True, default=None)
    is_customizable = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_on_sale = models.BooleanField(default=False)

    sale_start = models.DateTimeField(null=True, blank=True)
    sale_end = models.DateTimeField(null=True, blank=True)

    sale_label = models.CharField(
        max_length=50,
        default="Launch Offer",
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): 
        return self.name
    def is_sale_active(self):
        if not self.is_on_sale:
            return False

        now = timezone.now()
        if self.sale_start and self.sale_end:
            return self.sale_start <= now <= self.sale_end

        return False


    def get_display_price(self):
        if self.is_sale_active() and self.sale_price:
            return self.sale_price
        return self.base_price

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name="gallery"
    )
    image = CloudinaryField(
        "product_gallery_image"
    )
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Image for {self.product.name}"

class Attribute(models.Model):
    """Defines the type of attribute (e.g., Color, Size, Material)"""
    name = models.CharField(max_length=50) # e.g., "Color"

    def __str__(self):
        return self.name

class AttributeValue(models.Model):
    """Defines the specific value (e.g., Red, Blue, XL, XXL)"""
    attribute = models.ForeignKey(Attribute, related_name='values', on_delete=models.CASCADE)
    value = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

class ProductVariant(models.Model):
    """Links products to specific attribute combinations"""
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    attributes = models.ManyToManyField(AttributeValue)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        attrs = ", ".join([str(v) for v in self.attributes.all()])
        return f"{self.product.name} - {attrs}"


class PrintableArea(models.Model):
    """ 
    Defines available zones (Front, Back, Sleeve) for a product. 
    Coordinates are now optional, allowing for label-based placement.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="printable_areas")
    name = models.CharField(max_length=100) # e.g. "Front Center", "Back", "Left Sleeve"
    
    # Coordinates made optional for asset-based flow
    x = models.PositiveIntegerField(default=0, null=True, blank=True) 
    y = models.PositiveIntegerField(default=0, null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)      
    height = models.PositiveIntegerField(null=True, blank=True)     

    def __str__(self):
        return f"{self.product.name} - {self.name}"

class DesignPlacement(models.Model):
    """ 
    The final 'configured' product. Links a specific Design session 
    to a Product. This is what gets added to the Cart.
    """
    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="placements")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    # Made optional because the user's 'Overall Instructions' might define placement
    printable_area = models.ForeignKey(
        PrintableArea, 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    
    # layout_data remains for any specific scale/positioning metadata if needed
    layout_data = models.JSONField(null=True, blank=True) 
    
    # The generated image of the customized product
    preview_mockup = CloudinaryField(
        "preview_mockup",
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Placement: {self.product.name} ({self.design.id})"