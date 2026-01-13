# ==============================================
# CATALOG SIGNALS
# ==============================================
"""
Django signals for cache invalidation and image processing.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from PIL import Image
import os

from .models import Category, Product, PDFCatalog


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """
    Invalidate category-related caches when a category changes.
    """
    cache_keys = [
        'api_categories_list',
        'frontend_categories_with_counts',
        'home_categories',
    ]
    cache.delete_many(cache_keys)


@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """
    Invalidate product-related caches when a product changes.
    """
    cache_keys = [
        'api_products_featured',
        'api_products_promotional',
        'home_featured_products',
        'home_promo_products',
        'frontend_categories_with_counts',
    ]
    cache.delete_many(cache_keys)
    
    # Also invalidate category-specific caches
    if instance.category:
        cache.delete(f'category_products_{instance.category.slug}')


@receiver(post_save, sender=Product)
def create_product_thumbnail(sender, instance, created, **kwargs):
    """
    Create thumbnail image for product.
    Only runs if thumbnail doesn't exist.
    """
    if instance.image and not instance.image_thumbnail:
        try:
            create_thumbnail(instance)
        except Exception as e:
            # Log error but don't break save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create thumbnail: {e}")


def create_thumbnail(product, size=(300, 300)):
    """
    Create thumbnail from product image.
    """
    if not product.image:
        return
    
    try:
        img = Image.open(product.image.path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Generate thumbnail path
        base, ext = os.path.splitext(product.image.name)
        thumb_name = f"{base}_thumb{ext}"
        thumb_path = os.path.join(
            os.path.dirname(product.image.path),
            os.path.basename(thumb_name)
        )
        
        # Save thumbnail
        img.save(thumb_path, quality=85, optimize=True)
        
        # Update model without triggering signal again
        Product.objects.filter(pk=product.pk).update(
            image_thumbnail=thumb_name
        )
        
    except Exception as e:
        raise e


@receiver([post_save, post_delete], sender=PDFCatalog)
def invalidate_pdf_cache(sender, instance, **kwargs):
    """
    Invalidate PDF catalog cache.
    """
    cache.delete('latest_pdf_catalog')
    if instance.category:
        cache.delete(f'latest_pdf_catalog_{instance.category.slug}')
