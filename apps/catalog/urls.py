# ==============================================
# CATALOG API URLS
# ==============================================
"""
API URL routing for catalog endpoints.

Endpoints:
- /api/catalog/search/ - поиск товаров
- /api/catalog/search/suggestions/ - подсказки
- /api/catalog/recommendations/popular/ - популярные товары
- /api/catalog/recommendations/similar/<id>/ - похожие товары
- /api/catalog/products/<id>/view/ - увеличить счётчик просмотров
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, PDFCatalogViewSet
from .search_views import (
    SearchAPIView,
    SearchSuggestionsAPIView,
    PopularProductsAPIView,
    SimilarProductsAPIView,
    IncrementViewAPIView,
)

app_name = 'catalog_api'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'pdf-catalogs', PDFCatalogViewSet, basename='pdf-catalog')

urlpatterns = [
    # Router URLs (viewsets)
    path('', include(router.urls)),
    
    # Search API
    path('search/', SearchAPIView.as_view(), name='search'),
    path('search/suggestions/', SearchSuggestionsAPIView.as_view(), name='search-suggestions'),
    
    # Recommendations API
    path('recommendations/popular/', PopularProductsAPIView.as_view(), name='recommendations-popular'),
    path('recommendations/similar/<int:product_id>/', SimilarProductsAPIView.as_view(), name='recommendations-similar'),
    
    # Product view tracking
    path('products/<int:product_id>/view/', IncrementViewAPIView.as_view(), name='product-view'),
]

