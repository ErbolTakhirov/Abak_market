# ==============================================
# CATALOG FRONTEND VIEWS
# ==============================================
"""
Template-based views for catalog pages.
"""

from collections import OrderedDict
from django.views.generic import ListView, DetailView, TemplateView
from django.core.cache import cache
from django.db.models import Count, Q
from django.conf import settings

from .models import Category, Product


class MenuView(TemplateView):
    """
    Restaurant-style menu page with products grouped by category.
    Displays products in a 2x2 grid with warm beige design.
    Now supports smart search with fuzzy matching.
    """
    template_name = 'catalog/menu2.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        category_slug = self.request.GET.get('category')
        filter_type = self.request.GET.get('filter')
        search_query = self.request.GET.get('q', '').strip()
        
        # Import search service
        from .search_service import SmartSearchService
        
        # If there's a search query, use smart search
        if search_query:
            service = SmartSearchService()
            search_result = service.search(search_query, category_slug, limit=50)
            
            # Get categories for navigation
            categories = Category.objects.filter(
                is_active=True
            ).order_by('order', 'name')
            
            # Group search results by category
            products_by_category = OrderedDict()
            for product in search_result['products']:
                cat = product.category
                if cat not in products_by_category:
                    products_by_category[cat] = []
                products_by_category[cat].append(product)
            
            context['categories'] = categories
            context['products_by_category'] = products_by_category
            context['current_category'] = category_slug
            context['current_filter'] = filter_type
            context['search_query'] = search_query
            context['search_total'] = search_result['total']
            context['search_suggestions'] = search_result['suggestions']
            context['company_whatsapp'] = getattr(settings, 'COMPANY_WHATSAPP', '')
            
            return context
        
        # No search - regular mode
        # Base queryset
        products_qs = Product.objects.filter(
            is_available=True
        ).select_related('category').order_by('order', '-created_at')
        
        # Apply filters
        if category_slug:
            products_qs = products_qs.filter(category__slug=category_slug)
        
        if filter_type == 'popular':
            products_qs = products_qs.filter(is_featured=True)
        elif filter_type == 'new':
            products_qs = products_qs.filter(is_new=True)
        elif filter_type == 'promo':
            products_qs = products_qs.filter(is_promotional=True)
        
        # Get categories
        categories = Category.objects.filter(
            is_active=True
        ).order_by('order', 'name')
        
        # Group products by category
        products_by_category = OrderedDict()
        
        if category_slug:
            # Single category mode
            category = categories.filter(slug=category_slug).first()
            if category:
                category_products = list(products_qs.filter(category=category))
                if category_products:
                    products_by_category[category] = category_products
        else:
            # All categories mode - Optimized to avoid N+1 queries
            # Fetch all relevant products in one query
            all_products = list(products_qs)
            
            for category in categories:
                # Filter in Python instead of DB
                category_products = [p for p in all_products if p.category_id == category.id]
                if category_products:
                    products_by_category[category] = category_products
        
        context['categories'] = categories
        context['products_by_category'] = products_by_category
        context['current_category'] = category_slug
        context['current_filter'] = filter_type
        context['search_query'] = ''
        context['company_whatsapp'] = getattr(settings, 'COMPANY_WHATSAPP', '')
        
        return context


class CatalogListView(ListView):
    """
    Catalog page with all products and category filters.
    Restaurant-style design.
    """
    model = Product
    template_name = 'catalog/catalog_list_menu.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            is_available=True
        ).select_related('category').order_by('order', '-created_at')
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by type
        filter_type = self.request.GET.get('filter')
        if filter_type == 'promo':
            queryset = queryset.filter(is_promotional=True)
        elif filter_type == 'new':
            queryset = queryset.filter(is_new=True)
        elif filter_type == 'featured':
            queryset = queryset.filter(is_featured=True)
        
        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get categories with product counts
        cache_key = 'frontend_categories_with_counts'
        categories = cache.get(cache_key)
        
        if categories is None:
            categories = list(
                Category.objects.filter(is_active=True)
                .annotate(available_products_count=Count('products', filter=Q(products__is_available=True)))
                .order_by('order', 'name')
            )
            cache.set(cache_key, categories, 60 * 15)
        
        context['categories'] = categories
        context['current_category'] = self.request.GET.get('category')
        context['current_filter'] = self.request.GET.get('filter')
        context['search_query'] = self.request.GET.get('q', '')
        context['company_whatsapp'] = settings.COMPANY_WHATSAPP
        
        return context


class CategoryDetailView(DetailView):
    """
    Category page with products.
    Restaurant-style design.
    """
    model = Category
    template_name = 'catalog/category_detail_menu.html'
    context_object_name = 'category'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get products in category
        products = Product.objects.filter(
            category=self.object,
            is_available=True
        ).order_by('order', '-created_at')
        
        context['products'] = products
        context['company_whatsapp'] = settings.COMPANY_WHATSAPP
        
        # Get all categories for sidebar
        context['categories'] = Category.objects.filter(
            is_active=True
        ).order_by('order', 'name')
        
        return context


class ProductDetailView(DetailView):
    """
    Product detail page with restaurant-style design.
    Uses RecommendationService for similar products.
    """
    model = Product
    template_name = 'catalog/product_detail_menu.html'
    context_object_name = 'product'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(
            is_available=True
        ).select_related('category').prefetch_related('images')
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # Increment view count (async for performance)
        from .search_service import increment_product_view
        increment_product_view(self.object.id)
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use RecommendationService for similar products
        from .search_service import RecommendationService
        service = RecommendationService()
        
        # Get similar products with smart matching
        related = service.get_similar_products(self.object, limit=4)
        
        context['related_products'] = related
        context['company_whatsapp'] = settings.COMPANY_WHATSAPP
        context['whatsapp_url'] = self.object.get_whatsapp_order_url()
        
        # Categories for navigation
        context['categories'] = Category.objects.filter(
            is_active=True
        ).order_by('order', 'name')
        
        return context
