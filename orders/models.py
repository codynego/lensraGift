from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import Product, DesignPlacement, ProductVariant
import uuid

class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='cart_items'
    )
    session_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    # NEW: Link to the specific variation (Color/Size)
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    # The custom design layout
    placement = models.ForeignKey(
        DesignPlacement, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    secret_message = models.TextField(blank=True, null=True)
    emotion = models.CharField(max_length=50, blank=True, null=True)
    
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        # 1. Use variant price override if it exists
        # 2. Else use product base price
        price = self.product.base_price
        if self.variant and self.variant.price_override:
            price = self.variant.price_override
        return price * self.quantity

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.session_id[:8]})"
        variant_str = f" ({self.variant})" if self.variant else ""
        return f"{owner} - {self.product.name}{variant_str}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='orders'
    )
    guest_email = models.EmailField(max_length=255, blank=True, null=True)
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Shipping
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100, default='Nigeria')
    phone_number = models.CharField(max_length=20)
    
    # Payment
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, blank=True, null=True)
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    placement = models.ForeignKey(
        DesignPlacement, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    
    # --- SURPRISE REVEAL DATA (Captured from CartItem) ---
    secret_message = models.TextField(blank=True, null=True)
    emotion = models.CharField(max_length=50, blank=True, null=True)
    
    # This token is used for the unique QR code URL (e.g., lensra.com/reveal/[token])
    reveal_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, blank=True, null=True)
    
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2) 
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.unit_price:
            if self.variant and self.variant.price_override:
                self.unit_price = self.variant.price_override
            else:
                self.unit_price = self.product.base_price
        
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Order: {self.order.order_number})"