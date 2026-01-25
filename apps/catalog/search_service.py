# ==============================================
# SMART SEARCH SERVICE
# ==============================================
"""
Сервис умного поиска товаров с поддержкой:
- Fuzzy search (поиск с учётом опечаток)
- Синонимы и альтернативные написания
- Фильтрация по категориям
- Подсказки при вводе
- Рекомендации похожих товаров

Как настроить:
1. Добавьте синонимы через админку (Каталог -> Синонимы для поиска)
2. Настройте веса в SEARCH_WEIGHTS для изменения приоритетов
"""

import re
from difflib import SequenceMatcher
from django.db.models import Q, F, Value, IntegerField, Case, When
from django.db.models.functions import Length
from django.core.cache import cache

from .models import Product, Category, SearchSynonym, PopularSearch


# ==============================================
# КОНФИГУРАЦИЯ ПОИСКА (можно донастроить)
# ==============================================

SEARCH_CONFIG = {
    # Минимальный порог схожести для fuzzy search (0.0 - 1.0)
    'FUZZY_THRESHOLD': 0.6,
    
    # Максимум результатов в подсказках
    'SUGGESTIONS_LIMIT': 8,
    
    # Время кеширования результатов (секунды)
    'CACHE_TIMEOUT': 300,  # 5 минут
    
    # Веса для ранжирования результатов
    'WEIGHTS': {
        'exact_match': 100,      # Точное совпадение названия
        'starts_with': 80,       # Название начинается с запроса
        'word_match': 60,        # Слово из запроса в названии
        'description_match': 30, # Совпадение в описании
        'fuzzy_match': 20,       # Похожее написание
        'popular': 10,           # Бонус за популярность
        'featured': 5,           # Бонус за "популярные" товары
    }
}


class SmartSearchService:
    """
    Основной сервис для умного поиска товаров.
    
    Использование:
        service = SmartSearchService()
        results = service.search("кофе", category_slug="напитки")
        suggestions = service.get_suggestions("ко")
    """
    
    def __init__(self):
        self.config = SEARCH_CONFIG
    
    # ==============================================
    # ОСНОВНОЙ ПОИСК
    # ==============================================
    
    def search(self, query, category_slug=None, limit=50):
        """
        Выполняет умный поиск товаров.
        
        Args:
            query: поисковый запрос
            category_slug: фильтр по категории (опционально)
            limit: максимум результатов
            
        Returns:
            dict: {
                'products': список найденных товаров,
                'total': общее количество,
                'suggestions': альтернативные запросы (если мало результатов),
                'category': выбранная категория
            }
        """
        query = query.strip().lower() if query else ''
        
        if not query:
            return self._empty_result()
        
        # Проверяем кеш
        cache_key = f"search:{query}:{category_slug or 'all'}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Получаем все варианты запроса (с учётом синонимов)
        query_variants = SearchSynonym.get_normalized_queries(query)
        
        # Базовый queryset
        products_qs = Product.objects.filter(
            is_available=True
        ).select_related('category')
        
        # Фильтр по категории
        category = None
        if category_slug:
            category = Category.objects.filter(
                slug=category_slug, 
                is_active=True
            ).first()
            if category:
                products_qs = products_qs.filter(category=category)
        
        # Строим поисковый запрос
        search_q = self._build_search_query(query_variants)
        products_qs = products_qs.filter(search_q)
        
        # Добавляем ранжирование
        products_qs = self._add_ranking(products_qs, query)
        
        # Получаем результаты
        products = list(products_qs[:limit])
        total = products_qs.count()
        
        # Логируем поиск для статистики
        PopularSearch.log_search(query, total)
        
        # Готовим результат
        result = {
            'products': products,
            'total': total,
            'query': query,
            'category': category,
            'suggestions': [],
        }
        
        # Если мало результатов, добавляем подсказки
        if total < 3:
            result['suggestions'] = self._get_alternative_suggestions(query)
        
        # Кешируем
        cache.set(cache_key, result, self.config['CACHE_TIMEOUT'])
        
        return result
    
    def _build_search_query(self, query_variants):
        """
        Строит Q-объект для поиска по всем вариантам запроса.
        """
        q = Q()
        
        for variant in query_variants:
            # Поиск в названии
            q |= Q(name__icontains=variant)
            
            # Поиск в описании
            q |= Q(description__icontains=variant)
            q |= Q(short_description__icontains=variant)
            
            # Поиск по отдельным словам
            for word in variant.split():
                if len(word) >= 2:
                    q |= Q(name__icontains=word)
        
        return q
    
    def _add_ranking(self, queryset, query):
        """
        Добавляет ранжирование результатов по релевантности.
        """
        weights = self.config['WEIGHTS']
        
        # Аннотируем score для сортировки
        return queryset.annotate(
            search_score=Case(
                # Точное совпадение названия
                When(name__iexact=query, then=Value(weights['exact_match'])),
                # Название начинается с запроса
                When(name__istartswith=query, then=Value(weights['starts_with'])),
                # Запрос содержится в названии
                When(name__icontains=query, then=Value(weights['word_match'])),
                # Запрос в описании
                When(description__icontains=query, then=Value(weights['description_match'])),
                default=Value(weights['fuzzy_match']),
                output_field=IntegerField(),
            ) + Case(
                # Бонус за популярность (view_count)
                When(view_count__gte=100, then=Value(weights['popular'])),
                When(view_count__gte=50, then=Value(weights['popular'] // 2)),
                default=Value(0),
                output_field=IntegerField(),
            ) + Case(
                # Бонус за "популярные" товары
                When(is_featured=True, then=Value(weights['featured'])),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-search_score', '-view_count', 'order')
    
    def _get_alternative_suggestions(self, query):
        """
        Возвращает альтернативные поисковые запросы.
        """
        suggestions = []
        
        # Ищем похожие популярные запросы
        similar_queries = PopularSearch.objects.filter(
            results_count__gt=0
        ).exclude(query=query)[:20]
        
        for pq in similar_queries:
            similarity = self._calculate_similarity(query, pq.query)
            if similarity > self.config['FUZZY_THRESHOLD']:
                suggestions.append({
                    'query': pq.query,
                    'count': pq.results_count,
                    'similarity': similarity
                })
        
        # Сортируем по похожести
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)
        
        return suggestions[:5]
    
    def _calculate_similarity(self, str1, str2):
        """
        Вычисляет схожесть двух строк (0.0 - 1.0).
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _empty_result(self):
        """Возвращает пустой результат."""
        return {
            'products': [],
            'total': 0,
            'query': '',
            'category': None,
            'suggestions': [],
        }
    
    # ==============================================
    # ПОДСКАЗКИ (AUTOCOMPLETE)
    # ==============================================
    
    def get_suggestions(self, prefix, limit=None):
        """
        Возвращает подсказки для автодополнения.
        
        Args:
            prefix: начало запроса (минимум 2 символа)
            limit: максимум подсказок
            
        Returns:
            dict: {
                'products': товары, начинающиеся с prefix,
                'categories': подходящие категории,
                'queries': популярные запросы
            }
        """
        limit = limit or self.config['SUGGESTIONS_LIMIT']
        prefix = prefix.strip().lower() if prefix else ''
        
        if len(prefix) < 2:
            return {'products': [], 'categories': [], 'queries': []}
        
        # Кеш подсказок
        cache_key = f"suggestions:{prefix}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        result = {
            'products': self._suggest_products(prefix, limit),
            'categories': self._suggest_categories(prefix, limit // 2),
            'queries': self._suggest_queries(prefix, limit // 2),
        }
        
        cache.set(cache_key, result, 60)  # Кеш на 1 минуту
        
        return result
    
    def _suggest_products(self, prefix, limit):
        """Подсказки товаров."""
        products = Product.objects.filter(
            is_available=True,
            name__icontains=prefix
        ).select_related('category').order_by(
            # Сначала те, что начинаются с prefix
            Case(
                When(name__istartswith=prefix, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            '-view_count',
            'name'
        )[:limit]
        
        return [
            {
                'id': p.id,
                'name': p.name,
                'slug': p.slug,
                'price': str(p.price),
                'formatted_price': p.formatted_price,
                'category': p.category.name,
                'category_icon': p.category.icon,
                'image_url': p.image.url if p.image else None,
            }
            for p in products
        ]
    
    def _suggest_categories(self, prefix, limit):
        """Подсказки категорий."""
        categories = Category.objects.filter(
            is_active=True,
            name__icontains=prefix
        ).annotate(
            prod_count=models.Count('products', filter=Q(products__is_available=True))
        ).order_by('-prod_count')[:limit]
        
        return [
            {
                'id': c.id,
                'name': c.name,
                'slug': c.slug,
                'icon': c.icon,
                'products_count': c.prod_count,
            }
            for c in categories
        ]
    
    def _suggest_queries(self, prefix, limit):
        """Подсказки из популярных запросов."""
        queries = PopularSearch.get_suggestions(prefix, limit)
        
        return [
            {
                'query': q.query,
                'count': q.search_count,
            }
            for q in queries
        ]


# ==============================================
# СЕРВИС РЕКОМЕНДАЦИЙ
# ==============================================

class RecommendationService:
    """
    Сервис рекомендаций товаров.
    
    Логика рекомендаций (простая и прозрачная):
    1. Популярные товары - по view_count и purchase_count
    2. Похожие товары - из той же категории + по цене
    3. Новинки - is_new=True
    
    Использование:
        service = RecommendationService()
        popular = service.get_popular_products(limit=8)
        similar = service.get_similar_products(product, limit=4)
    """
    
    def get_popular_products(self, limit=8, exclude_ids=None):
        """
        Возвращает популярные товары для главной страницы.
        
        Сортировка:
        1. По количеству покупок (purchase_count)
        2. По количеству просмотров (view_count)
        3. По флагу is_featured
        
        Args:
            limit: количество товаров
            exclude_ids: список ID товаров для исключения
        """
        qs = Product.objects.filter(
            is_available=True
        ).select_related('category')
        
        if exclude_ids:
            qs = qs.exclude(id__in=exclude_ids)
        
        # Вычисляем "популярность" как комбинацию факторов
        qs = qs.annotate(
            popularity_score=F('purchase_count') * 3 + F('view_count') + Case(
                When(is_featured=True, then=Value(100)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-popularity_score', '-created_at')
        
        return list(qs[:limit])
    
    def get_similar_products(self, product, limit=4):
        """
        Возвращает похожие товары для страницы товара.
        
        Логика:
        1. Товары из той же категории
        2. С похожей ценой (±30%)
        3. Исключаем сам товар
        
        Args:
            product: товар, для которого ищем похожие
            limit: количество похожих товаров
        """
        # Диапазон цены ±30%
        price_min = float(product.price) * 0.7
        price_max = float(product.price) * 1.3
        
        # Сначала ищем в той же категории с похожей ценой
        similar = Product.objects.filter(
            is_available=True,
            category=product.category,
            price__gte=price_min,
            price__lte=price_max
        ).exclude(
            id=product.id
        ).select_related('category').order_by(
            '-view_count', 
            '-is_featured',
            'order'
        )[:limit]
        
        # Если мало похожих, добавляем просто из категории
        similar_list = list(similar)
        if len(similar_list) < limit:
            more = Product.objects.filter(
                is_available=True,
                category=product.category
            ).exclude(
                id__in=[product.id] + [p.id for p in similar_list]
            ).select_related('category').order_by(
                '-view_count',
                'order'
            )[:limit - len(similar_list)]
            
            similar_list.extend(more)
        
        # Если всё ещё мало, добавляем популярные из других категорий
        if len(similar_list) < limit:
            more = Product.objects.filter(
                is_available=True,
                is_featured=True
            ).exclude(
                id__in=[product.id] + [p.id for p in similar_list]
            ).select_related('category').order_by(
                '-view_count'
            )[:limit - len(similar_list)]
            
            similar_list.extend(more)
        
        return similar_list
    
    def get_new_products(self, limit=8):
        """
        Возвращает новые товары.
        """
        return list(
            Product.objects.filter(
                is_available=True,
                is_new=True
            ).select_related('category').order_by(
                '-created_at'
            )[:limit]
        )
    
    def get_promo_products(self, limit=8):
        """
        Возвращает акционные товары.
        """
        return list(
            Product.objects.filter(
                is_available=True,
                is_promotional=True
            ).select_related('category').order_by(
                '-view_count',
                'order'
            )[:limit]
        )


# ==============================================
# ФУНКЦИЯ ИНКРЕМЕНТА ПРОСМОТРОВ
# ==============================================

def increment_product_view(product_id):
    """
    Увеличивает счётчик просмотров товара.
    Используется на странице товара.
    
    Args:
        product_id: ID товара
    """
    Product.objects.filter(id=product_id).update(
        view_count=F('view_count') + 1
    )


# Импорт models для аннотаций в _suggest_categories
from django.db import models
