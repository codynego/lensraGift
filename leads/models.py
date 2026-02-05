import uuid
from django.db import models

class Lead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    whatsapp = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)

    invited_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals"
    )

    has_viewed_preview = models.BooleanField(default=False)
    has_shared = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.whatsapp



class InviteLink(models.Model):
    code = models.CharField(max_length=12, unique=True)
    owner = models.ForeignKey(Lead, on_delete=models.CASCADE)
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class GiftPreview(models.Model):
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE)
    preview_type = models.CharField(
        max_length=50,
        choices=[
            ("mug", "Mug"),
            ("frame", "Frame"),
            ("box", "Gift Box"),
        ]
    )
    blurred_image = models.ImageField(upload_to="previews/")
    created_at = models.DateTimeField(auto_now_add=True)


class WhatsAppLog(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=50)  # welcome, reminder, followup
    sent_at = models.DateTimeField(auto_now_add=True)
