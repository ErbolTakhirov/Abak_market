# ==============================================
# CATALOG FRONTEND URLS
# ==============================================
"""
Frontend URL routing for catalog pages.
"""

from django.urls import path
from .frontend_views import (
    MenuView,
    CategoryDetailView,
    ProductDetailView
)

app_name = 'catalog'

urlpatterns = [
    path('menu/', MenuView.as_view(), name='menu'),
    path('category/<slug:slug>/', CategoryDetailView.as_view(), name='category'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product'),
]
