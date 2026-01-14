from django.db import models
from django.conf import settings

class RewardProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,  # Fixed: changed from on_current_user
        related_name='reward_profile'
    )
    points = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} - {self.points} pts"

class RewardTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Spent'),
    )

    profile = models.ForeignKey(
        RewardProfile, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    amount = models.IntegerField()  # Positive for earn, negative for spend
    description = models.CharField(max_length=255) 
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    coupon_code = models.CharField(max_length=20, blank=True, null=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class RewardPerk(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    point_cost = models.PositiveIntegerField()
    # Tip: You can store the Lucide icon name here (e.g., 'Zap', 'Gift', 'Ticket')
    icon_name = models.CharField(max_length=50, default='Gift') 
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title