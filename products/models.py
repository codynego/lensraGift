from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from designs.models import Design
from cloudinary.models import CloudinaryField

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
    
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
    is_customizable = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self): 
        return self.name

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