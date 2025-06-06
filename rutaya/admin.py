from django.contrib import admin
from .models import Category, Destination


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'destinations_count', 'created_at']
    search_fields = ['name']
    ordering = ['name']

    def destinations_count(self, obj):
        return obj.destinations.count()

    destinations_count.short_description = 'Destinations'


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'location', 'category', 'created_at']
    list_filter = ['category', 'location', 'created_at']
    search_fields = ['name', 'location', 'description']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'category')
        }),
        ('Details', {
            'fields': ('description', 'image_url')
        }),
    )