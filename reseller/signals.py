from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import ResellerProfile, WalletTransaction
from orders.models import Order

@receiver(post_save, sender=Order)
def distribute_cashback(sender, instance, created, **kwargs):
    # 1. Skip if the order is newly created (it can't be delivered yet)
    if created:
        return

    # 2. Check if the status is 'delivered'
    if instance.status == 'delivered':
        # PREVENT DUPLICATE CASHBACK: Check if a transaction already exists for this order
        if WalletTransaction.objects.filter(order=instance, transaction_type='CASHBACK').exists():
            return

        try:
            # Check if the user has a reseller profile
            if not instance.user:
                return
                
            profile = instance.user.reseller_profile
            
            if profile.status == 'APPROVED':
                cashback_amount = instance.total_amount * Decimal('0.05')
                
                # Update Wallet Balance
                profile.wallet_balance += cashback_amount
                profile.save()

                # Record Transaction
                WalletTransaction.objects.create(
                    reseller=profile,
                    order=instance,
                    amount=cashback_amount,
                    transaction_type='CASHBACK',
                    description=f"5% Cashback for Order #{instance.order_number}"
                )
        except ResellerProfile.DoesNotExist:
            pass