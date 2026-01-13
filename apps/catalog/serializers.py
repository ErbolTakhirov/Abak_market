# ==============================================
# CATALOG SERIALIZERS
# ==============================================
"""
REST API serializers for catalog data.
"""

from rest_framework import serializers
from .models import Category, Product, ProductImage, PDFCatalog


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for category list/detail views.
    """
    products_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'category_type',
            'image', 'icon', 'products_count', 'is_active'
        ]


class CategoryMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal category serializer for product listings.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for additional product images.
    """
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'order']


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for product list views.
    Optimized with minimal data for faster loading.
    """
    category = CategoryMinimalSerializer(read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    whatsapp_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'short_description',
            'price', 'old_price', 'currency', 'formatted_price',
            'discount_percent', 'unit', 'image', 'is_available',
            'is_featured', 'is_promotional', 'is_new', 'weight',
            'whatsapp_url'
        ]
    
    def get_whatsapp_url(self, obj):
        return obj.get_whatsapp_order_url()


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full product serializer for detail views.
    """
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    whatsapp_url = serializers.SerializerMethodField()
    whatsapp_text = serializers.CharField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'description',
            'short_description', 'price', 'old_price', 'currency',
            'formatted_price', 'discount_percent', 'unit', 'min_quantity',
            'image', 'images', 'is_available', 'is_featured',
            'is_promotional', 'is_new', 'weight', 'calories',
            'ingredients', 'whatsapp_url', 'whatsapp_text',
            'created_at', 'updated_at'
        ]
    
    def get_whatsapp_url(self, obj):
        return obj.get_whatsapp_order_url()


class ProductWhatsAppSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for WhatsApp bot responses.
    """
    formatted_price = serializers.CharField(read_only=True)
    whatsapp_text = serializers.CharField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'formatted_price', 'image',
            'short_description', 'whatsapp_text', 'is_available'
        ]


class PDFCatalogSerializer(serializers.ModelSerializer):
    """
    Serializer for PDF catalogs.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = PDFCatalog
        fields = ['id', 'name', 'file', 'category', 'category_name', 'updated_at']
