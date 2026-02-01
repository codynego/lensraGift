import random
import string
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from orders.models import Coupon

def generate_unique_coupon():
    return "LENSRA-" + ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=6)
    )


def generate_coupon_for_email(email):

    coupon_code = generate_unique_coupon()
    expiry_date = timezone.now() + timedelta(days=7)

    Coupon.objects.create(
        code=coupon_code,
        discount_type=Coupon.PERCENTAGE,
        value=10,  # 10% discount
        expires_at=expiry_date,
        max_uses=1,
        email=email
    )

    return coupon_code