# ==============================================
# CATALOG API URLS
# ==============================================
"""
API URL routing for catalog endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, PDFCatalogViewSet

app_name = 'catalog_api'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'pdf-catalogs', PDFCatalogViewSet, basename='pdf-catalog')

urlpatterns = [
    path('', include(router.urls)),
]
