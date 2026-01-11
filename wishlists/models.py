from django.db import models
from django.conf import settings
from products.models import Product 

class Wishlist(models.Model):
    """Container model for a user's wishlist."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wishlist'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name}'s Wishlist"

    @property
    def item_count(self):
        return self.items.count()

class WishlistItem(models.Model):
    """Individual products added to a wishlist."""
    wishlist = models.ForeignKey(
        Wishlist, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product_id')
        ordering = ['-added_at']

    def __str__(self):
        return f"Item in {self.wishlist.user.email}'s Wishlist"