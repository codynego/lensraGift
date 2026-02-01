from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order
from core.tasks.orders import send_order_confirmation_email, send_order_recieved_email

@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    if created:
        send_order_confirmation_email.delay(instance.id)
        send_order_recieved_email.delay(instance.id)


@receiver(post_save, sender=Order)
def order_paid(sender, instance, **kwargs):
    """Signal handler for when an order is paid."""
    if instance.is_paid and instance.status == 'processing':
        # Logic after payment is confirmed
        # For example: notify warehouse, send confirmation email, etc.
        pass
