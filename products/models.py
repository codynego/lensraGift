from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from designs.models import Design

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
    def __str__(self): return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="products"
    )
    
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_customizable = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.name

class PrintableArea(models.Model):
    """ Defines where the canvas sits on the product image. """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="printable_areas")
    name = models.CharField(max_length=100) # e.g. "Front Center"
    x = models.PositiveIntegerField(default=0) # Top-left X coordinate on the product image
    y = models.PositiveIntegerField(default=0) # Top-left Y coordinate
    width = models.PositiveIntegerField()      # Canvas width
    height = models.PositiveIntegerField()     # Canvas height



class DesignPlacement(models.Model):
    """ The link between a Design and a specific Product Area. """
    design = models.ForeignKey(Design, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    printable_area = models.ForeignKey(PrintableArea, on_delete=models.CASCADE)
    layout_data = models.JSONField() # JSON specifically scaled for this area
    preview_mockup = models.ImageField(upload_to="mockups/", null=True) # Design overlaid on Product