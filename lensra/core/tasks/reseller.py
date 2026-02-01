# core/tasks.py
from celery import shared_task
from lensra.core.tasks.sendgrid import send_template_email
from django.conf import settings

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_reseller_application_email(self, reseller_id):
    from reseller.models import ResellerProfile

    try:
        reseller = ResellerProfile.objects.get(id=reseller_id)
    except ResellerProfile.DoesNotExist:
        return

    # Applicant email (if you want to notify them)
    applicant_email = reseller.user.email if reseller.user else None

    # Notify your team first
    team_email = settings.RESELLER_NOTIFICATION_EMAIL  # e.g., "sales@lensra.com"

    # Data for template
    dynamic_data = {
        "applicant_name": reseller.user.get_full_name() if reseller.user else "Applicant",
        "business_name": reseller.business_name,
        "whatsapp_number": reseller.whatsapp_number,
        "marketing_plan": reseller.marketing_plan,
    }

    # Send email to your team
    send_template_email(
        to_email=team_email,
        template_id=settings.SENDGRID_RESELLER_APPLICATION_TEAM_TEMPLATE_ID,
        dynamic_data=dynamic_data
    )

    # Optional: send confirmation email to applicant
    if applicant_email:
        send_template_email(
            to_email=applicant_email,
            template_id=settings.SENDGRID_RESELLER_APPLICATION_USER_TEMPLATE_ID,
            dynamic_data={
                "business_name": reseller.business_name,
                "user_name": reseller.user.get_full_name(),
            }
        )
