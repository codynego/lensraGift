from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    """Signal handler for when an order is created."""
    if created:
        # Additional logic when order is created
        # For example: send email notification, log activity, etc.
        pass


@receiver(post_save, sender=Order)
def order_paid(sender, instance, **kwargs):
    """Signal handler for when an order is paid."""
    if instance.is_paid and instance.status == 'processing':
        # Logic after payment is confirmed
        # For example: notify warehouse, send confirmation email, etc.
        pass
