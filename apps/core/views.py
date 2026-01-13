# ==============================================
# CORE VIEWS
# ==============================================
"""
Core views for the application including health checks and home page.
"""

from django.http import JsonResponse
from django.views.generic import TemplateView
from django.core.cache import cache
from django.db import connection
from django.conf import settings


def health_check(request):
    """
    Health check endpoint for load balancers and monitoring.
    Checks database and cache connectivity.
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'error: cache read failed'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['cache'] = f'error: {str(e)}'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


class HomeView(TemplateView):
    """
    Home page view with featured products and promotions.
    Restaurant-style design.
    """
    template_name = 'pages/home_menu.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Import here to avoid circular imports
        from apps.catalog.models import Product, Category
        
        # Get featured products (cached for 15 minutes)
        cache_key = 'home_featured_products'
        featured_products = cache.get(cache_key)
        
        if featured_products is None:
            featured_products = list(
                Product.objects.filter(
                    is_available=True,
                    is_featured=True
                ).select_related('category')[:8]
            )
            cache.set(cache_key, featured_products, 60 * 15)
        
        # Get promotional products
        cache_key = 'home_promo_products'
        promo_products = cache.get(cache_key)
        
        if promo_products is None:
            promo_products = list(
                Product.objects.filter(
                    is_available=True,
                    is_promotional=True
                ).select_related('category')[:4]
            )
            cache.set(cache_key, promo_products, 60 * 15)
        
        # Get categories for navigation
        cache_key = 'home_categories'
        categories = cache.get(cache_key)
        
        if categories is None:
            categories = list(
                Category.objects.filter(is_active=True)
                .order_by('order', 'name')
            )
            cache.set(cache_key, categories, 60 * 15)
        
        context.update({
            'featured_products': featured_products,
            'promo_products': promo_products,
            'categories': categories,
            'company_name': settings.COMPANY_NAME,
            'company_phone': settings.COMPANY_PHONE,
            'company_whatsapp': settings.COMPANY_WHATSAPP,
        })
        
        return context
