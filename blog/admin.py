from django.contrib import admin
from django import forms
from .models import BlogPost, BlogCategory
from django_ckeditor_5.widgets import CKEditor5Widget

# 1. Category Admin
@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

# 2. Blog Post Form with CKEditor
class BlogPostAdminForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = '__all__'
        widgets = {
            "content": CKEditor5Widget(config_name="extends"),
        }

# 3. Blog Post Admin
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm
    
    # Organize columns in the list view
    list_display = ('title', 'category', 'is_published', 'created_at')
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'content', 'keywords')
    prepopulated_fields = {'slug': ('title',)}
    
    # Organize the Edit Page into sections
    fieldsets = (
        ("Content Details", {
            'fields': ('title', 'slug', 'category', 'featured_image', 'content', 'is_published')
        }),
        ("SEO Settings (Google Search)", {
            'classes': ('collapse',), # This hides the section until you click it
            'fields': ('meta_title', 'meta_description', 'keywords', 'canonical_url'),
            'description': "Use these fields to improve Lensra's ranking on Google."
        }),
    )

    # Optional: Makes the save button stick to the top on long blog posts
    save_on_top = True