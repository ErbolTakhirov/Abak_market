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
        
        # Base filter for Menu: Only DISHES
        base_category_filter = Q(is_active=True, category_type=Category.CategoryType.DISHES)
        
        # If there's a search query, use smart search
        if search_query:
            service = SmartSearchService()
            # Note: Search service might need updating to support type filtering, 
            # but for now we filter the results or assume search is global.
            # Ideally we'd pass a filter to search service.
            # For immediate fix, let's filter the display categories.
            
            search_result = service.search(search_query, category_slug, limit=50)
            
            # Get categories for navigation (Only Dishes)
            categories = Category.objects.filter(base_category_filter).order_by('order', 'name')
            
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
        # Base queryset - Filter by DISHES category type
        products_qs = Product.objects.filter(
            is_available=True,
            category__category_type=Category.CategoryType.DISHES
        ).select_related('category').order_by('order', '-created_at')
        
        # Apply filters
        if category_slug:
            # Check if this category belongs to DISHES
            target_category = Category.objects.filter(slug=category_slug, is_active=True).first()
            if target_category and target_category.category_type != Category.CategoryType.DISHES:
                # Redirect to Catalog list if it's a product category
                from django.shortcuts import redirect
                from django.urls import reverse
                return redirect(reverse('catalog:list') + f'?category={category_slug}')
            
            products_qs = products_qs.filter(category__slug=category_slug)
        
        if filter_type == 'popular':
            products_qs = products_qs.filter(is_featured=True)
        elif filter_type == 'new':
            products_qs = products_qs.filter(is_new=True)
        elif filter_type == 'promo':
            products_qs = products_qs.filter(is_promotional=True)
        
        # Get categories (Only Dishes)
        categories = Category.objects.filter(base_category_filter).order_by('order', 'name')
        
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

    def get(self, request, *args, **kwargs):
        # Override get to handle redirection before template rendering
        category_slug = request.GET.get('category')
        if category_slug:
            target_category = Category.objects.filter(slug=category_slug, is_active=True).first()
            if target_category and target_category.category_type != Category.CategoryType.DISHES:
                from django.shortcuts import redirect
                from django.urls import reverse
                return redirect(reverse('catalog:list') + f'?category={category_slug}')
        return super().get(request, *args, **kwargs)


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
        # Base filter
        queryset = Product.objects.filter(is_available=True)
        
        # Search query
        search_query = self.request.GET.get('q', '').strip()
        
        if not search_query:
            # Regular mode: Filter for products that are NOT dishes (i.e. groceries)
            queryset = queryset.exclude(
                category__category_type=Category.CategoryType.DISHES
            )
        
        # Optimize queryset
        queryset = queryset.select_related('category').order_by('order', '-created_at')
        
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
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get categories with product counts (excluding dishes)
        # We don't cache this specific mixed query as easily, or we invalidate.
        # For safety/speed update, let's fetch directly or use a different cache key if needed.
        # Using a fresh query for correctness.
        
        categories = list(
            Category.objects.filter(is_active=True)
            .exclude(category_type=Category.CategoryType.DISHES)
            .annotate(available_products_count=Count('products', filter=Q(products__is_available=True)))
            .order_by('order', 'name')
        )
        
        context['categories'] = categories
        context['current_category'] = self.request.GET.get('category')
        context['current_filter'] = self.request.GET.get('filter')
        context['search_query'] = self.request.GET.get('q', '')
        context['company_whatsapp'] = getattr(settings, 'COMPANY_WHATSAPP', '')
        context['COMPANY_WHATSAPP'] = getattr(settings, 'COMPANY_WHATSAPP', '')
        
        return context

    def get(self, request, *args, **kwargs):
        # Handle redirection for Dishes categories
        category_slug = request.GET.get('category')
        if category_slug:
            target_category = Category.objects.filter(slug=category_slug, is_active=True).first()
            if target_category and target_category.category_type == Category.CategoryType.DISHES:
                from django.shortcuts import redirect
                from django.urls import reverse
                return redirect(reverse('catalog:menu') + f'?category={category_slug}')
        return super().get(request, *args, **kwargs)


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
        
        # Contextual Sidebar: Show categories of the SAME TYPE
        context['categories'] = Category.objects.filter(
            is_active=True,
            category_type=self.object.category_type
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
        
        # Contextual Sidebar: Show categories matching the product's category type
        context['categories'] = Category.objects.filter(
            is_active=True,
            category_type=self.object.category.category_type
        ).order_by('order', 'name')
        
        return context
