from django.contrib import admin
from .models import BlogPost
from django_ckeditor_5.widgets import CKEditor5Widget
from django import forms

class BlogPostAdminForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = '__all__'
        widgets = {
            "content": CKEditor5Widget(config_name="extends"),
        }

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm # <--- This forces the widget to load
    list_display = ('title', 'is_published', 'created_at')
    prepopulated_fields = {'slug': ('title',)}