from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class ResellerProfile(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Active Reseller'),
        ('SUSPENDED', 'Suspended'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reseller_profile'
    )
    
    # Application Data
    whatsapp_number = models.CharField(max_length=20)
    marketing_plan = models.TextField(help_text="Where do you plan to sell?")
    business_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Status & Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # The Wallet
    wallet_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    def __str__(self):
        return f"{self.user.email} - {self.status}"

    class Meta:
        verbose_name = "Reseller Profile"



class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('CASHBACK', 'Order Cashback'),
        ('WITHDRAWAL', 'Bank Withdrawal'),
        ('PAYMENT', 'Order Payment'), # If they use wallet to pay for new orders
    ]

    reseller = models.ForeignKey(
        ResellerProfile, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    order = models.ForeignKey(
        'orders.Order', # Adjust this path to your Order model
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.reseller.user.email})"