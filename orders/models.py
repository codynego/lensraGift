from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import Product, DesignPlacement, ProductVariant
import uuid


from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

    DISCOUNT_TYPE_CHOICES = [
        (PERCENTAGE, "Percentage"),
        (FIXED, "Fixed Amount"),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES
    )
    value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Leave empty for unlimited use"
    )
    used_count = models.PositiveIntegerField(default=0)

    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def can_be_used(self):
        if not self.is_active:
            return False
        if self.is_expired():
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def __str__(self):
        return self.code


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



class ShippingZone(models.Model):
    name = models.CharField(max_length=100) # e.g., "Lagos Mainland", "Lagos Island", "North Major Cities"
    base_fee = models.DecimalField(max_digits=10, decimal_places=2) # e.g., 2500.00

    

    def __str__(self):

        return f"{self.name} - ₦{self.base_fee}"



class ShippingLocation(models.Model):
    city_name = models.CharField(max_length=100) # e.g., "Ikeja", "Surulere", "Garki"
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name="locations")

    

    def __str__(self):

        return f"{self.city_name} ({self.zone.name})"



class ShippingOption(models.Model):
    name = models.CharField(max_length=100) # e.g., "Standard", "Express/Same Day"
    additional_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    estimated_delivery = models.CharField(max_length=100) # e.g., "3-5 days" or "Within 24 hours"

    def __str__(self):

        return f"{self.name} (+ ₦{self.additional_cost})"


from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


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
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # -----------------
    # Financial Totals
    # -----------------

    # Items only (before shipping & discount)
    subtotal_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    # Items + shipping (before discount)
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # -------- Coupon Snapshot --------
    applied_coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    # ---------------------------------

    # Final amount to be paid (THIS is what payment gateway sees)
    payable_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # -----------------
    # Shipping Links & Snapshots
    # -----------------
    shipping_location = models.ForeignKey(
        'ShippingLocation',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    shipping_option = models.ForeignKey(
        'ShippingOption',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )

    # Hard snapshots (never change)
    shipping_base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    shipping_option_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    # ---------------------------------

    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100, default='Nigeria')
    phone_number = models.CharField(max_length=20)

    # -----------------
    # Payment
    # -----------------
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True
    )
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number}"

    @property
    def total_shipping_cost(self):
        return self.shipping_base_cost + self.shipping_option_cost




class CouponRedemption(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Change from "auth.User" to this
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)


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
    # In your OrderItem model
    reveal_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    
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