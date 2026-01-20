from django.db import models

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


class AddOn(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class DigitalGiftAddOn(models.Model):
    gift = models.ForeignKey(DigitalGift, on_delete=models.CASCADE, related_name='addons')
    addon = models.ForeignKey(AddOn, on_delete=models.CASCADE)


class GiftStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    SENT = 'sent', 'Sent'
    DELIVERED = 'delivered', 'Delivered'

