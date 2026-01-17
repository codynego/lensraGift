from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class Design(models.Model):
    """
    The main container for a custom design session. 
    Stores the high-level instructions and the final rendered preview.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='designs',
        null=True, blank=True  # Allow guest designs if needed
    )
    name = models.CharField(max_length=255, blank=True)
    
    # Customization Data from the Editor
    custom_text = models.CharField(max_length=255, blank=True, null=True)
    overall_instructions = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    # Visuals
    preview_image = CloudinaryField(
        "design_preview_image",
        blank=True,
        null=True
    )
    is_featured = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        user_email = self.user.email if self.user else "Guest"
        return f"Design {self.id} ({self.name or 'Untitled'}) by {user_email}"


class DesignImage(models.Model):
    """
    Stores individual images uploaded within a single design session,
    along with specific placement notes for each.
    """
    design = models.ForeignKey(
        Design, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = CloudinaryField(
        "design_asset_image"
    )
    placement_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Asset for Design {self.design.id}"