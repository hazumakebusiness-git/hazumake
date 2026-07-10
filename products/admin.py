

# Register your models here.
# product/admin.py
from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from hazu.core.svg_image import SVGImageAdminMixin
from .models import Product, Game, Category

@admin.register(Game)
class GameAdmin(SVGImageAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'short_name', 'field_preset', 'is_active', 'is_featured', 'sort_order', 'product_count']
    list_editable = ['is_active', 'is_featured', 'sort_order']
    list_filter = ['is_active', 'is_featured', 'field_preset']
    search_fields = ['name', 'short_name', 'slug']
    prepopulated_fields = {'slug': ('short_name',)}
    readonly_fields = ['id', 'created_at', 'icon_preview', 'banner_preview']
    fieldsets = (
        ('Basic Info', {'fields': ('id', 'name', 'short_name', 'slug', 'description')}),
        ('Media', {'fields': ('icon', 'icon_preview', 'banner', 'banner_preview')}),
        ('Checkout Config', {'fields': ('field_preset', 'checkout_fields'), 
         'description': 'checkout_fields is a JSON array. Use field_preset as reference.'}),
        ('Supplier', {'fields': ('supplier_game_code',)}),
        ('Display', {'fields': ('is_active', 'is_featured', 'sort_order')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
    
    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    product_count.short_description = 'Active Products'

    def icon_preview(self, obj):
        if obj and obj.icon:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 240px; object-fit: contain; border: 1px solid #ddd;" />',
                obj.icon.url,
            )
        return '-'
    icon_preview.short_description = 'Icon Preview'

    def banner_preview(self, obj):
        if obj and obj.banner:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 240px; object-fit: contain; border: 1px solid #ddd;" />',
                obj.banner.url,
            )
        return '-'
    banner_preview.short_description = 'Banner Preview'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(SVGImageAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'game', 'category', 'type', 'diamond_amount', 'price_coins', 'price_inr', 'is_active']
    list_editable = ['is_active', 'price_coins', 'price_inr']
    list_filter = ['game', 'category', 'type', 'is_active']
    search_fields = ['name', 'game__name', 'category__name']
    autocomplete_fields = ['category']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 240px; object-fit: contain; border: 1px solid #ddd;" />',
                obj.image.url,
            )
        return '-'
    image_preview.short_description = 'Image Preview'