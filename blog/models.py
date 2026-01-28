from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from cloudinary.models import CloudinaryField

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Blog Categories"

    def __str__(self):
        return self.name

class BlogPost(models.Model):
    # Link to Category
    category = models.ForeignKey(
        BlogCategory, 
        on_report=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="posts"
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    featured_image = CloudinaryField(
        "blog_featured_image",
        blank=True,
        null=True
    )
    
    content = CKEditor5Field('Content', config_name='extends')
    
    # SEO Fields
    meta_title = models.CharField(
        max_length=60, 
        blank=True, 
        null=True,
        help_text="The title that appears in Google search. Keep under 60 characters."
    )
    meta_description = models.TextField(
        max_length=160, 
        blank=True, 
        null=True,
        help_text="The short summary under the link in Google. Keep under 160 characters."
    )
    keywords = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Comma-separated keywords (e.g., gift shop, benin city, birthday surprise)"
    )
    canonical_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="Only use this if you are re-posting an article from another site."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title