from django.db import models
from django.conf import settings
from products.models import Product
from PIL import Image
import os


class Design(models.Model):
    """User-uploaded designs for customizing products."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='designs')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='designs')
    name = models.CharField(max_length=255)
    design_image = models.ImageField(upload_to='designs/')
    preview_image = models.ImageField(upload_to='design_previews/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} by {self.user.email}"

    def save(self, *args, **kwargs):
        """Override save to generate preview image."""
        super().save(*args, **kwargs)
        if self.design_image and not self.preview_image:
            self.generate_preview()

    def generate_preview(self):
        """Generate a preview image for the design."""
        try:
            img = Image.open(self.design_image.path)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            preview_name = f"preview_{os.path.basename(self.design_image.name)}"
            preview_path = os.path.join(
                settings.MEDIA_ROOT, 'design_previews', preview_name
            )
            
            os.makedirs(os.path.dirname(preview_path), exist_ok=True)
            img.save(preview_path)
            
            self.preview_image = f'design_previews/{preview_name}'
            Design.objects.filter(pk=self.pk).update(preview_image=self.preview_image)
        except Exception as e:
            print(f"Error generating preview: {e}")
