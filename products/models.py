from django.db import models
from django.core.validators import MinValueValidator


class Product(models.Model):
    """Base product model for print-on-demand items."""

    name = models.CharField(max_length=255)
    description = models.TextField()
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class PrintableArea(models.Model):
    """Defines printable areas on a product."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='printable_areas')
    name = models.CharField(max_length=100)
    x_position = models.IntegerField(help_text='X coordinate of printable area')
    y_position = models.IntegerField(help_text='Y coordinate of printable area')
    width = models.IntegerField(help_text='Width of printable area in pixels')
    height = models.IntegerField(help_text='Height of printable area in pixels')
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"
