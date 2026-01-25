# ==============================================
# CATALOG ADMIN CONFIGURATION
# ==============================================
"""
Admin interface for product and category management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

from .models import Category, Product, ProductImage, PDFCatalog, SearchSynonym, PopularSearch


class ProductImageInline(admin.TabularInline):
    """Inline for additional product images."""
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin for product categories.
    """
    
    list_display = (
        'icon', 'name', 'category_type', 'products_count_display',
        'is_active', 'show_on_home', 'order'
    )
    list_display_links = ('name',)
    list_filter = ('category_type', 'is_active', 'show_on_home')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    list_editable = ('order', 'is_active', 'show_on_home')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'category_type')
        }),
        (_('Изображение'), {
            'fields': ('image', 'icon')
        }),
        (_('Настройки'), {
            'fields': ('order', 'is_active', 'show_on_home')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _products_count=Count('products', filter=models.Q(products__is_available=True))
        )
    
    def products_count_display(self, obj):
        """Display products count."""
        count = getattr(obj, '_products_count', obj.products_count)
        return format_html(
            '<span style="font-weight: bold;">{}</span> товаров',
            count
        )
    products_count_display.short_description = _('Товаров')
    products_count_display.admin_order_field = '_products_count'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin for products with full management capabilities.
    """
    
    list_display = (
        'image_preview', 'name', 'category', 'price_display',
        'is_available', 'is_featured', 'is_promotional', 'view_count', 'updated_at'
    )
    list_display_links = ('name',)
    list_filter = (
        'category', 'is_available', 'is_featured', 
        'is_promotional', 'is_new', 'currency'
    )
    search_fields = ('name', 'description', 'ingredients')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', '-created_at')
    list_editable = ('is_available', 'is_featured', 'is_promotional')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'image_preview_large', 'view_count', 'purchase_count')
    raw_id_fields = ('category',)
    inlines = [ProductImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'description', 'short_description')
        }),
        (_('Цена'), {
            'fields': ('price', 'old_price', 'currency', 'unit', 'min_quantity')
        }),
        (_('Изображения'), {
            'fields': ('image', 'image_preview_large', 'image_thumbnail')
        }),
        (_('Статус'), {
            'fields': ('is_available', 'is_featured', 'is_promotional', 'is_new', 'order')
        }),
        (_('Дополнительно'), {
            'fields': ('weight', 'calories', 'ingredients'),
            'classes': ('collapse',)
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        (_('Статистика'), {
            'fields': ('view_count', 'purchase_count'),
            'classes': ('collapse',)
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """Small image preview in list."""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = _('Фото')
    
    def image_preview_large(self, obj):
        """Large image preview in form."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />',
                obj.image.url
            )
        return _('Изображение не загружено')
    image_preview_large.short_description = _('Превью')
    
    def price_display(self, obj):
        """Display formatted price with discount."""
        if obj.old_price:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{}</span> '
                '<span style="color: #e74c3c; font-weight: bold;">{}</span> '
                '<span style="background: #27ae60; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">-{}%</span>',
                obj.old_price,
                obj.formatted_price,
                obj.discount_percent
            )
        return format_html('<span style="font-weight: bold;">{}</span>', obj.formatted_price)
    price_display.short_description = _('Цена')
    
    actions = ['make_available', 'make_unavailable', 'make_featured', 'remove_featured']
    
    @admin.action(description=_('Сделать доступными'))
    def make_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} товаров теперь в наличии')
    
    @admin.action(description=_('Сделать недоступными'))
    def make_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} товаров сняты с продажи')
    
    @admin.action(description=_('Добавить в популярные'))
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} товаров добавлены в популярные')
    
    @admin.action(description=_('Убрать из популярных'))
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} товаров убраны из популярных')


@admin.register(PDFCatalog)
class PDFCatalogAdmin(admin.ModelAdmin):
    """
    Admin for PDF catalogs.
    """
    
    list_display = ('name', 'category', 'is_active', 'file_link', 'updated_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name',)
    ordering = ('-updated_at',)
    list_editable = ('is_active',)
    
    def file_link(self, obj):
        """Link to download PDF."""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📄 Скачать</a>',
                obj.file.url
            )
        return '-'
    file_link.short_description = _('Файл')


# Import models for admin_order_field
from django.db import models


# ==============================================
# SEARCH ADMIN
# ==============================================

@admin.register(SearchSynonym)
class SearchSynonymAdmin(admin.ModelAdmin):
    """
    Админка для синонимов поиска.
    Здесь можно добавлять альтернативные написания слов и опечатки.
    """
    list_display = ('word', 'synonym')
    list_filter = ('word',)
    search_fields = ('word', 'synonym')
    ordering = ('word', 'synonym')


@admin.register(PopularSearch)
class PopularSearchAdmin(admin.ModelAdmin):
    """
    Админка для просмотра популярных поисковых запросов.
    """
    list_display = ('query', 'search_count', 'results_count', 'last_searched')
    list_filter = ('last_searched',)
    search_fields = ('query',)
    ordering = ('-search_count',)
    readonly_fields = ('query', 'search_count', 'results_count', 'last_searched')
    
    def has_add_permission(self, request):
        return False  # Запросы создаются автоматически
