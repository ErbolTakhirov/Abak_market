# ==============================================
# CATALOG CELERY TASKS
# ==============================================
"""
Background tasks for catalog operations.
"""

from celery import shared_task
from django.core.cache import cache
from django.db.models import Count, Q
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.catalog.tasks.sync_catalog_cache')
def sync_catalog_cache():
    """
    Periodic task to warm up catalog caches.
    Runs every 15 minutes.
    """
    from .models import Category, Product
    from .serializers import CategorySerializer, ProductListSerializer
    
    try:
        # Cache categories
        categories = Category.objects.filter(is_active=True).annotate(
            products_count=Count('products', filter=Q(products__is_available=True))
        ).order_by('order', 'name')
        
        category_data = CategorySerializer(categories, many=True).data
        cache.set('api_categories_list', category_data, 60 * 20)
        
        # Cache featured products
        featured = Product.objects.filter(
            is_available=True,
            is_featured=True
        ).select_related('category')[:12]
        
        featured_data = ProductListSerializer(featured, many=True).data
        cache.set('api_products_featured', featured_data, 60 * 20)
        
        # Cache promotional products
        promo = Product.objects.filter(
            is_available=True,
            is_promotional=True
        ).select_related('category')[:12]
        
        promo_data = ProductListSerializer(promo, many=True).data
        cache.set('api_products_promotional', promo_data, 60 * 20)
        
        logger.info('Catalog cache synced successfully')
        return {'status': 'success', 'categories': len(categories)}
        
    except Exception as e:
        logger.error(f'Failed to sync catalog cache: {e}')
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.catalog.tasks.generate_pdf_catalog')
def generate_pdf_catalog(category_id=None):
    """
    Generate PDF catalog for all products or specific category.
    """
    from .models import Category, Product, PDFCatalog
    from .pdf_generator import CatalogPDFGenerator
    
    try:
        # Get products
        products = Product.objects.filter(is_available=True).select_related('category')
        
        category = None
        if category_id:
            category = Category.objects.get(id=category_id)
            products = products.filter(category=category)
        
        # Generate PDF
        generator = CatalogPDFGenerator()
        pdf_path = generator.generate(products, category)
        
        # Create or update PDFCatalog record
        name = f"Каталог - {category.name}" if category else "Полный каталог"
        
        catalog, created = PDFCatalog.objects.update_or_create(
            category=category,
            defaults={
                'name': name,
                'file': pdf_path,
                'is_active': True
            }
        )
        
        logger.info(f'PDF catalog generated: {catalog.name}')
        return {'status': 'success', 'catalog_id': catalog.id}
        
    except Exception as e:
        logger.error(f'Failed to generate PDF catalog: {e}')
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.catalog.tasks.optimize_product_images')
def optimize_product_images():
    """
    Optimize all product images that haven't been optimized.
    """
    from .models import Product
    from PIL import Image
    import os
    
    optimized_count = 0
    
    products = Product.objects.filter(
        image__isnull=False
    ).exclude(image='')
    
    for product in products:
        try:
            # Check if storage supports local path
            try:
                img_path = product.image.path
                if not os.path.exists(img_path):
                    continue
            except (AttributeError, NotImplementedError):
                # Storage doesn't support local path (like Cloudinary/S3)
                # Cloudinary usually handles optimization automatically
                continue
            
            img = Image.open(img_path)
            
            # Resize if too large
            max_size = (1200, 1200)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Save optimized
                img.save(img_path, 'JPEG', quality=85, optimize=True)
                optimized_count += 1
                
        except Exception as e:
            logger.error(f'Failed to optimize image for product {product.id}: {e}')
            continue
    
    logger.info(f'Optimized {optimized_count} product images')
    return {'status': 'success', 'optimized': optimized_count}
