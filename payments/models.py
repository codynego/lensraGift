from django.db import models
from django.conf import settings
from orders.models import Order

class Payment(models.Model):
    """Model to track payments for both logged-in users and guests."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    
    # Made nullable so guests can pay without an account
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='payments',
        null=True, 
        blank=True
    )
    
    # Session ID to track guest payments
    session_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    reference = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, default='paystack')
    
    # Paystack specific fields
    access_code = models.CharField(max_length=255, blank=True)
    authorization_url = models.URLField(blank=True)
    paystack_response = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.reference} - {self.status}"