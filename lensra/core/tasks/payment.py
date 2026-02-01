from celery import shared_task
from lensra.core.tasks.sendgrid import send_template_email
from django.conf import settings

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_payment_confirmation_email(self, payment_id):
    from payments.models import Payment  # import inside task to avoid circular imports

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return  # payment not found

    # Only send email if payment succeeded
    if payment.status.lower() != 'success':
        return

    # Determine recipient
    email = payment.user.email if payment.user else None
    if not email and payment.order:
        email = payment.order.guest_email
    if not email:
        return  # no email to send

    # Prepare dynamic data for SendGrid template
    dynamic_data = {
        "payment_reference": payment.reference,
        "amount": str(payment.amount),
        "payment_method": payment.payment_method.title(),
        "order_number": payment.order.order_number if payment.order else None,
        "coupon_code": payment.order.applied_coupon.code if payment.order and payment.order.applied_coupon else None,
        "shipping_address": payment.order.shipping_address if payment.order else None,
        "shipping_city": payment.order.shipping_city if payment.order else None,
        "shipping_state": payment.order.shipping_state if payment.order else None,
        "shipping_country": payment.order.shipping_country if payment.order else None,
        "phone_number": payment.order.phone_number if payment.order else None,
    }

    send_template_email(
        to_email=email,
        template_id=settings.SENDGRID_PAYMENT_SUCCESS_TEMPLATE_ID,
        dynamic_data=dynamic_data
    )
