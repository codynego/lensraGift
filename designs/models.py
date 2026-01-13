from django.db import models
from django.conf import settings
from PIL import Image
import os


class Design(models.Model):
    """User-uploaded designs for customizing products."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='designs')
    name = models.CharField(max_length=255)
    is_featured = models.BooleanField(default=False)
    design_data = models.JSONField(null=True, blank=True)  # Store Fabric.js canvas JSON
    preview_image = models.ImageField(upload_to='designs/', null=True, blank=True)  # Store preview PNG
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} by {self.user.email}"