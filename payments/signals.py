# payments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from payments.models import Payment
from lensra.core.tasks.payment import send_payment_confirmation_email

@receiver(post_save, sender=Payment)
def payment_success_email(sender, instance, created, **kwargs):
    if not created and instance.status.lower() == 'success':
        send_payment_confirmation_email.delay(instance.id)
