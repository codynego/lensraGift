from celery import shared_task
from core.emails.sendgrid import send_template_email
from django.conf import settings


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_welcome_email(self, email, coupon_code):
    send_template_email(
        to_email=email,
        template_id=settings.SENDGRID_WELCOME_TEMPLATE_ID,
        dynamic_data={
            "coupon_code": coupon_code,
            "expiry_days": 7,
        }
    )

