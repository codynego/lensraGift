from django.db import models
import string
import secrets



def generate_gift_code():
    """
    Generates a 6-character unique ID using a mix of upper, lower, 
    and digits while excluding visually similar characters (I, l, 1, O, 0).
    """
    # Custom alphabet for maximum clarity and high variety
    # Removed: I, l, 1, O, o, 0
    alphabet = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    
    return ''.join(secrets.choice(alphabet) for _ in range(6))


class GiftStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    SENT = 'sent', 'Sent'
    DELIVERED = 'delivered', 'Delivered'


class Occasion(models.Model):
    name = models.CharField(max_length=100)  # Birthday, Love, Friendship
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class ExperienceTier(models.Model):
    name = models.CharField(max_length=50)  # Basic, Standard, Premium
    description = models.TextField()  # Features included
    price = models.DecimalField(max_digits=10, decimal_places=2)
    recommended = models.BooleanField(default=False)  # Highlighted tier

    def __str__(self):
        return f"{self.name} - ₦{self.price}"



class DigitalGift(models.Model):
    # Sender info
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    session_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    short_id = models.CharField(max_length=10, default=generate_gift_code, editable=False,db_index=True, null=False, blank=False)

    # Recipient info
    recipient_name = models.CharField(max_length=100)
    recipient_email = models.EmailField()
    recipient_phone = models.CharField(max_length=20, blank=True, null=True)

    # Occasion & tier
    occasion = models.ForeignKey(Occasion, on_delete=models.SET_NULL, null=True)
    tier = models.ForeignKey(ExperienceTier, on_delete=models.SET_NULL, null=True)

    # Message fields
    text_message = models.TextField(blank=True)
    voice_message = models.FileField(upload_to='voice_messages/', blank=True, null=True)
    video_message = models.FileField(upload_to='video_messages/', blank=True, null=True)
    is_opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(blank=True, null=True)
    open_count = models.PositiveIntegerField(default=0)

    # Delivery
    scheduled_delivery = models.DateTimeField(blank=True, null=True)
    delivered = models.BooleanField(default=False)
    delivery_method = models.CharField(
        max_length=50,
        choices=[
            ('email', 'Email'),
            ('whatsapp', 'WhatsApp'),
            ('link', 'Private Link')
        ],
        default='email'
    )
    status = models.CharField(max_length=20,
        choices=GiftStatus.choices,
        default=GiftStatus.PENDING
    )
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Gift from {self.sender_name} to {self.recipient_name}"

    @property
    def total_price(self):
        # Start with the tier price
        total = self.tier.price if self.tier else 0
        
        # Add the price of all related addons
        # We use .addons.all() because of the related_name in DigitalGiftAddOn
        for gift_addon in self.addons.all():
            total += gift_addon.addon.price
            
        return total

    def save(self, *args, **kwargs):
            if not self.short_id:
                # Collision check
                new_id = generate_gift_code()
                while DigitalGift.objects.filter(short_id=new_id).exists():
                    new_id = generate_gift_code()
                self.short_id = new_id
            super().save(*args, **kwargs)


class AddOn(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class DigitalGiftAddOn(models.Model):
    gift = models.ForeignKey(DigitalGift, on_delete=models.CASCADE, related_name='addons')
    addon = models.ForeignKey(AddOn, on_delete=models.CASCADE)


