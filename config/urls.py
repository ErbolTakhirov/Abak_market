# ==============================================
# GROCERY STORE - MAIN URL CONFIGURATION
# ==============================================
"""
URL Configuration for Grocery Store + WhatsApp Bot
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from apps.core.views import health_check, HomeView


urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Health check for load balancers
    path('health/', health_check, name='health_check'),
    
    # API endpoints
    path('api/', include([
        path('catalog/', include('apps.catalog.urls')),
        path('orders/', include('apps.orders.urls')),
        path('whatsapp/', include('apps.whatsapp_bot.urls')),
        path('payments/', include('apps.payments.urls')),
        path('dialogs/', include('apps.dialogs.urls')),
    ])),
    
    # Frontend pages
    path('', HomeView.as_view(), name='home'),
    path('catalog/', include('apps.catalog.frontend_urls')),
    path('contacts/', TemplateView.as_view(template_name='pages/contacts_menu.html'), name='contacts'),
    
    # Robots.txt and sitemap
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', 
        content_type='text/plain'
    ), name='robots'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass


# Custom admin site configuration
admin.site.site_header = 'Продуктовый Магазин "Свежесть"'
admin.site.site_title = 'Админ-панель'
admin.site.index_title = 'Управление магазином'
