# ==============================================
# SEARCH API VIEWS
# ==============================================
"""
API endpoints для умного поиска и рекомендаций.

Endpoints:
- GET /api/catalog/search/ - поиск товаров
- GET /api/catalog/search/suggestions/ - подсказки при вводе
- GET /api/catalog/recommendations/popular/ - популярные товары
- GET /api/catalog/recommendations/similar/<product_id>/ - похожие товары
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from .search_service import SmartSearchService, RecommendationService, increment_product_view
from .models import Product, Category
from .serializers import ProductListSerializer as ProductSerializer, CategorySerializer


class SearchAPIView(APIView):
    """
    API для поиска товаров.
    
    GET /api/catalog/search/
    
    Параметры:
        q (str): поисковый запрос (обязательный)
        category (str): slug категории для фильтрации (опционально)
        limit (int): максимум результатов (по умолчанию 50)
    
    Ответ:
        {
            "success": true,
            "query": "запрос",
            "total": 10,
            "category": {...} или null,
            "products": [...],
            "suggestions": [...] (если мало результатов)
        }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        category_slug = request.GET.get('category', None)
        limit = min(int(request.GET.get('limit', 50)), 100)
        
        if not query:
            return Response({
                'success': False,
                'error': 'Параметр q обязателен',
                'products': [],
                'total': 0,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Выполняем поиск
        service = SmartSearchService()
        result = service.search(query, category_slug, limit)
        
        # Сериализуем товары
        products_data = ProductSerializer(result['products'], many=True).data
        
        # Категория
        category_data = None
        if result['category']:
            category_data = CategorySerializer(result['category']).data
        
        return Response({
            'success': True,
            'query': query,
            'total': result['total'],
            'category': category_data,
            'products': products_data,
            'suggestions': result['suggestions'],
        })


class SearchSuggestionsAPIView(APIView):
    """
    API для подсказок при вводе (autocomplete).
    
    GET /api/catalog/search/suggestions/
    
    Параметры:
        q (str): начало запроса (минимум 2 символа)
        limit (int): максимум подсказок (по умолчанию 8)
    
    Ответ:
        {
            "success": true,
            "products": [...],
            "categories": [...],
            "queries": [...]
        }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        prefix = request.GET.get('q', '').strip()
        limit = min(int(request.GET.get('limit', 8)), 20)
        
        if len(prefix) < 2:
            return Response({
                'success': True,
                'products': [],
                'categories': [],
                'queries': [],
            })
        
        service = SmartSearchService()
        result = service.get_suggestions(prefix, limit)
        
        return Response({
            'success': True,
            **result
        })


class PopularProductsAPIView(APIView):
    """
    API для получения популярных товаров.
    
    GET /api/catalog/recommendations/popular/
    
    Параметры:
        limit (int): количество товаров (по умолчанию 8)
    
    Ответ:
        {
            "success": true,
            "products": [...]
        }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        limit = min(int(request.GET.get('limit', 8)), 20)
        
        service = RecommendationService()
        products = service.get_popular_products(limit)
        
        return Response({
            'success': True,
            'products': ProductSerializer(products, many=True).data
        })


class SimilarProductsAPIView(APIView):
    """
    API для получения похожих товаров.
    
    GET /api/catalog/recommendations/similar/<product_id>/
    
    Параметры:
        limit (int): количество товаров (по умолчанию 4)
    
    Ответ:
        {
            "success": true,
            "products": [...]
        }
    """
    permission_classes = [AllowAny]
    
    def get(self, request, product_id):
        limit = min(int(request.GET.get('limit', 4)), 10)
        
        try:
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Товар не найден',
                'products': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        service = RecommendationService()
        similar = service.get_similar_products(product, limit)
        
        return Response({
            'success': True,
            'products': ProductSerializer(similar, many=True).data
        })


class IncrementViewAPIView(APIView):
    """
    API для увеличения счётчика просмотров товара.
    
    POST /api/catalog/products/<product_id>/view/
    
    Ответ:
        {
            "success": true
        }
    """
    permission_classes = [AllowAny]
    
    def post(self, request, product_id):
        try:
            increment_product_view(product_id)
            return Response({'success': True})
        except Exception:
            return Response({'success': False}, status=status.HTTP_400_BAD_REQUEST)
