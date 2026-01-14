from django.contrib import admin
from .models import Design, DesignImage

class DesignImageInline(admin.TabularInline):
    model = DesignImage
    extra = 1
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.image.url)
        return "-"

@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'custom_text', 'created_at', 'is_featured']
    list_filter = ['is_featured', 'created_at']
    search_fields = ['user__email', 'custom_text', 'overall_instructions']
    inlines = [DesignImageInline]