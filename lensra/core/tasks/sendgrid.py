from celery import shared_task
from django.conf import settings
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To



def send_template_email(to_email: str, template_id: str, dynamic_data: dict):
    """
    Sends a SendGrid template email.

    Args:
        to_email (str): Recipient email address
        template_id (str): SendGrid dynamic template ID
        dynamic_data (dict): Dict of template variables
    """
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=To(to_email),
    )
    message.template_id = template_id
    message.dynamic_template_data = dynamic_data

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {to_email} | Status: {response.status_code}")
    except Exception as e:
        print(f"SendGrid error sending to {to_email}: {e}")
        raise e



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

