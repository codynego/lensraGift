from celery import shared_task
from core.tasks.sendgrid import send_template_email
from django.conf import settings

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_order_confirmation_email(self, order_id):
    from orders.models import Order  # import inside task to avoid circular imports

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return  # nothing to do

    email = order.user.email if order.user else order.guest_email
    if not email:
        return  # no email to send

    # Prepare dynamic data for SendGrid template
    dynamic_data = {
        "order_number": order.order_number,
        "subtotal": str(order.subtotal_amount),
        "shipping_cost": str(order.total_shipping_cost),
        "discount": str(order.discount_amount),
        "total": str(order.payable_amount),
        "shipping_address": order.shipping_address,
        "shipping_city": order.shipping_city,
        "shipping_state": order.shipping_state,
        "shipping_country": order.shipping_country,
        "phone_number": order.phone_number,
        "coupon_code": order.applied_coupon.code if order.applied_coupon else None,
    }

    send_template_email(
        to_email=email,
        template_id=settings.SENDGRID_ORDER_CONFIRMATION_TEMPLATE_ID,
        dynamic_data=dynamic_data
    )




@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_order_recieved_email(self, order_id):
    from orders.models import Order  # import inside task to avoid circular imports

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return  # nothing to do

    email = order.user.email if order.user else order.guest_email
    if not email:
        return  # no email to send

    # Prepare dynamic data for SendGrid template
    dynamic_data = {
        "order_number": order.order_number,
        "subtotal": str(order.subtotal_amount),
        "shipping_cost": str(order.total_shipping_cost),
        "discount": str(order.discount_amount),
        "total": str(order.payable_amount),
        "shipping_address": order.shipping_address,
        "shipping_city": order.shipping_city,
        "shipping_state": order.shipping_state,
        "shipping_country": order.shipping_country,
        "phone_number": order.phone_number,
        "coupon_code": order.applied_coupon.code if order.applied_coupon else None,
    }

    send_template_email(
        to_email=settings.ORDER_TEAM_EMAIL,
        template_id=settings.SENDGRID_ORDER_RECEIVED_TEMPLATE_ID,
        dynamic_data=dynamic_data
    )

