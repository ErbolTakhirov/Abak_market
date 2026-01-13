# ==============================================
# CATALOG API VIEWS
# ==============================================
"""
REST API views for catalog endpoints.
"""

from django.db.models import Count, Q
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Category, Product, PDFCatalog
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWhatsAppSerializer,
    PDFCatalogSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for categories.
    
    list: Get all active categories
    retrieve: Get category by slug
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.annotate(
            products_count=Count('products', filter=Q(products__is_available=True))
        ).order_by('order', 'name')
    
    def list(self, request, *args, **kwargs):
        """Cached category list."""
        cache_key = 'api_categories_list'
        cached = cache.get(cache_key)
        
        if cached is not None:
            return Response(cached)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 60 * 15)  # 15 minutes
        
        return response
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get products in category."""
        category = self.get_object()
        products = Product.objects.filter(
            category=category,
            is_available=True
        ).select_related('category').order_by('order', '-created_at')
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for products.
    
    list: Get all available products with filtering
    retrieve: Get product by slug
    """
    queryset = Product.objects.filter(is_available=True)
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'is_promotional', 'is_new']
    search_fields = ['name', 'description', 'ingredients']
    ordering_fields = ['price', 'created_at', 'name', 'order']
    ordering = ['order', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        if self.action == 'whatsapp':
            return ProductWhatsAppSerializer
        return ProductListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('category')
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products."""
        cache_key = 'api_products_featured'
        cached = cache.get(cache_key)
        
        if cached is not None:
            return Response(cached)
        
        products = self.get_queryset().filter(is_featured=True)[:12]
        serializer = ProductListSerializer(products, many=True)
        
        cache.set(cache_key, serializer.data, 60 * 15)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def promotional(self, request):
        """Get promotional products."""
        cache_key = 'api_products_promotional'
        cached = cache.get(cache_key)
        
        if cached is not None:
            return Response(cached)
        
        products = self.get_queryset().filter(is_promotional=True)[:12]
        serializer = ProductListSerializer(products, many=True)
        
        cache.set(cache_key, serializer.data, 60 * 15)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def whatsapp(self, request):
        """
        Get products formatted for WhatsApp bot.
        Supports category filter via query param.
        """
        category_id = request.query_params.get('category')
        queryset = self.get_queryset()
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        products = queryset[:20]
        serializer = ProductWhatsAppSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def whatsapp_card(self, request, slug=None):
        """Get single product formatted for WhatsApp."""
        product = self.get_object()
        serializer = ProductWhatsAppSerializer(product)
        return Response(serializer.data)


class PDFCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for PDF catalogs.
    """
    queryset = PDFCatalog.objects.filter(is_active=True)
    serializer_class = PDFCatalogSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest catalog, optionally filtered by category."""
        category_id = request.query_params.get('category')
        
        if category_id:
            catalog = PDFCatalog.objects.filter(
                is_active=True,
                category_id=category_id
            ).first()
        else:
            catalog = PDFCatalog.objects.filter(
                is_active=True,
                category__isnull=True
            ).first()
        
        if not catalog:
            # Fallback to any active catalog
            catalog = PDFCatalog.objects.filter(is_active=True).first()
        
        if catalog:
            serializer = self.get_serializer(catalog)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Каталог не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
