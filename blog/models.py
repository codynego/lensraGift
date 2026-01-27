from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    featured_image = models.ImageField(upload_to='blog_images/')
    # This field provides the Bold, Fonts, and Styling tools
    content = CKEditor5Field('Content', config_name='extends') 
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title