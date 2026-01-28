# Архитектура Каталога продуктового магазина

> Документация по проектированию вкладки «Каталог» для сайта продуктового магазина
> Соответствует ТЗ и интегрируется с WhatsApp-ботом

---

## 📋 Содержание

1. [Структура базы данных](#1-структура-базы-данных)
2. [API-эндпоинты](#2-api-эндпоинты)
3. [Логика фронтенда](#3-логика-фронтенда)
4. [Интеграция с WhatsApp-ботом](#4-интеграция-с-whatsapp-ботом)
5. [Чек-лист соответствия ТЗ](#5-чек-лист-соответствия-тз)

---

## 1. Структура базы данных

### 1.1 ER-диаграмма

```
┌─────────────────────┐       ┌──────────────────────────────┐
│     Category        │       │          Product             │
├─────────────────────┤       ├──────────────────────────────┤
│ id (PK)             │───┐   │ id (PK)                      │
│ name                │   │   │ name [Название]              │
│ slug (unique)       │   └──►│ category_id (FK) [Категория] │
│ description         │       │ description [Описание]       │
│ category_type       │       │ short_description            │
│ image               │       │ price [Цена]                 │
│ icon (emoji)        │       │ old_price                    │
│ order               │       │ currency [Валюта]            │
│ is_active           │       │ unit                         │
│ show_on_home        │       │ image [Изображение]          │
│ created_at          │       │ image_thumbnail              │
│ updated_at          │       │ is_available [Статус наличия]│
└─────────────────────┘       │ is_featured                  │
                              │ is_promotional               │
                              │ is_new                       │
                              │ weight                       │
                              │ calories                     │
                              │ ingredients                  │
                              │ view_count                   │
                              │ purchase_count               │
                              │ order                        │
                              │ created_at                   │
                              │ updated_at                   │
                              │ slug (unique)                │
                              └──────────────────────────────┘
                                           │
                                           ▼
                              ┌──────────────────────────────┐
                              │       ProductImage           │
                              ├──────────────────────────────┤
                              │ id (PK)                      │
                              │ product_id (FK)              │
                              │ image                        │
                              │ alt_text                     │
                              │ order                        │
                              └──────────────────────────────┘
```

### 1.2 Модель Product (Товар) — Поля по ТЗ

| Поле | Тип | Описание | Требование ТЗ |
|------|-----|----------|---------------|
| `name` | CharField(200) | Название товара | ✅ название |
| `category` | ForeignKey(Category) | Связь с категорией | ✅ категория |
| `description` | TextField | Полное описание | ✅ описание |
| `short_description` | CharField(300) | Краткое описание для карточек/WhatsApp | ✅ описание |
| `price` | DecimalField(10,2) | Текущая цена | ✅ цена |
| `currency` | CharField(3) | Код валюты (KGS, RUB, USD, EUR, KZT) | ✅ валюта |
| `image` | ImageField | Основное изображение | ✅ изображение |
| `is_available` | BooleanField | Статус наличия | ✅ статус наличия |

### 1.3 Индексы для быстрой работы

```python
class Meta:
    indexes = [
        models.Index(fields=['is_available', 'is_featured']),  # Фильтрация по наличию
        models.Index(fields=['category', 'is_available']),     # Категории + наличие
        models.Index(fields=['slug']),                         # Быстрый поиск по slug
    ]
```

### 1.4 SQL-схема (для справки)

```sql
-- Категории
CREATE TABLE catalog_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    category_type VARCHAR(20) DEFAULT 'products',
    image VARCHAR(100),
    icon VARCHAR(10) DEFAULT '🛒',
    "order" INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    show_on_home BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Товары
CREATE TABLE catalog_product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(220) UNIQUE NOT NULL,
    category_id INTEGER NOT NULL REFERENCES catalog_category(id),
    description TEXT NOT NULL,
    short_description VARCHAR(300) DEFAULT '',
    price DECIMAL(10,2) NOT NULL,
    old_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'KGS',
    unit VARCHAR(20) DEFAULT 'шт',
    min_quantity INTEGER DEFAULT 1,
    image VARCHAR(100) NOT NULL,
    image_thumbnail VARCHAR(100),
    is_available BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_promotional BOOLEAN DEFAULT FALSE,
    is_new BOOLEAN DEFAULT FALSE,
    weight VARCHAR(50) DEFAULT '',
    calories INTEGER,
    ingredients TEXT DEFAULT '',
    view_count INTEGER DEFAULT 0,
    purchase_count INTEGER DEFAULT 0,
    "order" INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Индексы
CREATE INDEX idx_product_available_featured ON catalog_product(is_available, is_featured);
CREATE INDEX idx_product_category_available ON catalog_product(category_id, is_available);
CREATE INDEX idx_product_slug ON catalog_product(slug);
```

---

## 2. API-эндпоинты

### 2.1 Базовые эндпоинты каталога

| Метод | Эндпоинт | Описание | Кэширование |
|-------|----------|----------|-------------|
| `GET` | `/api/catalog/categories/` | Список всех активных категорий | 15 мин |
| `GET` | `/api/catalog/categories/{slug}/` | Детали категории | - |
| `GET` | `/api/catalog/categories/{slug}/products/` | Товары в категории | - |
| `GET` | `/api/catalog/products/` | Список всех товаров (с фильтрами) | - |
| `GET` | `/api/catalog/products/{slug}/` | Детали товара | - |
| `GET` | `/api/catalog/products/featured/` | Популярные товары | 15 мин |
| `GET` | `/api/catalog/products/promotional/` | Акционные товары | 15 мин |

### 2.2 Эндпоинты для WhatsApp-бота

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/api/catalog/products/whatsapp/` | Товары в формате для WhatsApp |
| `GET` | `/api/catalog/products/{slug}/whatsapp_card/` | Карточка товара для WhatsApp |
| `GET` | `/api/catalog/pdf-catalogs/latest/` | Последний PDF-каталог |

### 2.3 Эндпоинты поиска и рекомендаций

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/api/catalog/search/?q={query}` | Поиск товаров |
| `GET` | `/api/catalog/search/suggestions/?q={prefix}` | Подсказки для автодополнения |
| `GET` | `/api/catalog/recommendations/popular/` | Популярные товары |
| `GET` | `/api/catalog/recommendations/similar/{id}/` | Похожие товары |
| `POST` | `/api/catalog/products/{id}/view/` | Увеличить счётчик просмотров |

### 2.4 Параметры фильтрации продуктов

```
GET /api/catalog/products/?category={id|slug}&is_featured=true&is_promotional=true&is_new=true
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `category` | string/int | Фильтр по категории (slug или id) |
| `is_featured` | bool | Только популярные |
| `is_promotional` | bool | Только акционные |
| `is_new` | bool | Только новинки |
| `search` | string | Текстовый поиск |
| `ordering` | string | Сортировка: `price`, `-price`, `name`, `created_at` |

### 2.5 Пример ответов API

#### GET `/api/catalog/products/` — Список товаров

```json
[
  {
    "id": 1,
    "name": "Помидоры свежие",
    "slug": "pomidory-svezhie",
    "category": {
      "id": 1,
      "name": "Овощи",
      "slug": "ovoschi",
      "icon": "🥕"
    },
    "short_description": "Свежие спелые помидоры с грядки",
    "price": "150.00",
    "old_price": null,
    "currency": "KGS",
    "formatted_price": "150 сом",
    "discount_percent": 0,
    "unit": "кг",
    "image": "/media/products/tomatoes.jpg",
    "is_available": true,
    "is_featured": true,
    "is_promotional": false,
    "is_new": false,
    "weight": "1 кг",
    "whatsapp_url": "https://wa.me/996XXXXXXXXX?text=..."
  }
]
```

#### GET `/api/catalog/products/{slug}/` — Детали товара

```json
{
  "id": 1,
  "name": "Помидоры свежие",
  "slug": "pomidory-svezhie",
  "category": {
    "id": 1,
    "name": "Овощи",
    "slug": "ovoschi",
    "description": "Свежие овощи и зелень",
    "icon": "🥕",
    "products_count": 15
  },
  "description": "Спелые сочные помидоры, выращенные на местных фермах. Идеальны для салатов и соусов.",
  "short_description": "Свежие спелые помидоры с грядки",
  "price": "150.00",
  "old_price": "180.00",
  "currency": "KGS",
  "formatted_price": "150 сом",
  "discount_percent": 17,
  "unit": "кг",
  "min_quantity": 1,
  "image": "/media/products/tomatoes.jpg",
  "images": [
    {"id": 1, "image": "/media/products/tomatoes-2.jpg", "alt_text": "Помидоры крупным планом"}
  ],
  "is_available": true,
  "is_featured": true,
  "is_promotional": true,
  "is_new": false,
  "weight": "1 кг",
  "calories": 20,
  "ingredients": "",
  "whatsapp_url": "https://wa.me/996XXXXXXXXX?text=...",
  "whatsapp_text": "*Помидоры свежие*\n💰 150 сом\n📦 1 кг\n\nСвежие спелые помидоры с грядки",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-28T09:00:00Z"
}
```

### 2.6 Эндпоинт для быстрого обновления цен

```python
# Административный API для массового обновления цен
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def bulk_update_prices(request):
    """
    PATCH /api/catalog/products/bulk-prices/
    
    Body:
    {
        "updates": [
            {"id": 1, "price": "160.00"},
            {"id": 2, "price": "250.00", "old_price": "300.00"}
        ]
    }
    """
    updates = request.data.get('updates', [])
    updated = []
    
    for item in updates:
        try:
            product = Product.objects.get(id=item['id'])
            product.price = item['price']
            if 'old_price' in item:
                product.old_price = item.get('old_price')
            product.save(update_fields=['price', 'old_price', 'updated_at'])
            updated.append(product.id)
        except Product.DoesNotExist:
            continue
    
    # Инвалидация кэша
    cache.delete_many(['api_products_featured', 'api_products_promotional'])
    
    return Response({'updated': updated})
```

---

## 3. Логика фронтенда

### 3.1 Архитектура страницы каталога

```
┌────────────────────────────────────────────────────────────┐
│                    HEADER (Шапка)                          │
│  🏠 Главная    📍 Адрес магазина    📞 Контакты            │
├────────────────────────────────────────────────────────────┤
│                  ПОИСК                                     │
│  🔍 [Поиск товаров...                              ]       │
├────────────────────────────────────────────────────────────┤
│                КАТЕГОРИИ (горизонтальный скролл)           │
│  [Все] [🥕 Овощи] [🍎 Фрукты] [🥛 Молочные] [🍖 Мясо] ...  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│              СЕТКА КАРТОЧЕК ТОВАРОВ                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ 📷      │ │ 📷 -20% │ │ 📷      │ │ 📷 NEW  │           │
│  │ Товар 1 │ │ Товар 2 │ │ Товар 3 │ │ Товар 4 │           │
│  │ 150 сом │ │ 200 сом │ │ 90 сом  │ │ 250 сом │           │
│  │[Корзина]│ │[Корзина]│ │[Корзина]│ │[Корзина]│           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ ...     │ │ ...     │ │ ...     │ │ ...     │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                            │
├────────────────────────────────────────────────────────────┤
│              КНОПКА "ОТКРЫТЬ КОРЗИНУ"                      │
│          [ 🛒 Открыть корзину (3 товара) ]                 │
├────────────────────────────────────────────────────────────┤
│              НИЖНЯЯ НАВИГАЦИЯ (fixed)                      │
│    🏠 Главная     🛒 Корзина     📞 Контакты               │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Компоненты карточки товара

```html
<div class="menu-card" id="product-{{ product.id }}">
    <!-- Бейдж (скидка/новинка/хит) -->
    <span class="menu-card-badge">-20%</span>
    
    <!-- Изображение с ленивой загрузкой -->
    <a href="/catalog/product/{{ product.slug }}/" class="menu-card-image">
        <img src="{{ product.image.url }}" 
             alt="{{ product.name }}" 
             loading="lazy"
             decoding="async">
    </a>
    
    <!-- Контент -->
    <div class="menu-card-content">
        <h3 class="menu-card-name">{{ product.name }}</h3>
        
        <div class="menu-card-price">
            <span class="menu-card-old-price">{{ product.formatted_old_price }}</span>
            {{ product.formatted_price }}
            <span class="menu-card-weight">{{ product.weight }}</span>
        </div>
        
        <button class="menu-card-add-btn add-to-cart-btn"
                data-id="{{ product.id }}"
                data-name="{{ product.name }}"
                data-price="{{ product.price }}"
                data-image="{{ product.image.url }}">
            В корзину
        </button>
    </div>
</div>
```

### 3.3 Логика фильтрации по категориям

```javascript
// Фронтенд фильтрация через URL параметры
const categoryTabs = document.querySelectorAll('.menu-nav-item');

categoryTabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
        // URL формат: /menu/?category=ovoschi
        const categorySlug = tab.dataset.category;
        
        if (categorySlug) {
            window.location.href = `/menu/?category=${categorySlug}`;
        } else {
            window.location.href = '/menu/';
        }
    });
});
```

### 3.4 Быстрая загрузка изображений

```html
<!-- Стратегия оптимизации изображений -->

<!-- 1. Lazy loading для изображений ниже fold -->
<img loading="lazy" decoding="async" src="..." alt="...">

<!-- 2. Preload для критичных изображений первого экрана -->
<link rel="preload" as="image" href="/media/products/hero-product.webp">

<!-- 3. Использование responsive images -->
<picture>
    <source srcset="/media/products/tomatoes-400.webp" 
            media="(max-width: 480px)" type="image/webp">
    <source srcset="/media/products/tomatoes-800.webp" 
            media="(max-width: 768px)" type="image/webp">
    <img src="/media/products/tomatoes.jpg" alt="Помидоры">
</picture>

<!-- 4. CSS placeholder для предотвращения layout shift -->
<style>
.menu-card-image {
    aspect-ratio: 4/3;
    background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
}
</style>
```

```python
# Бэкенд: Автоматическое создание thumbnail при загрузке
from django.db.models.signals import post_save
from PIL import Image
import io

def create_thumbnail(sender, instance, **kwargs):
    if instance.image and not instance.image_thumbnail:
        img = Image.open(instance.image)
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        thumb_io = io.BytesIO()
        img.save(thumb_io, format='WEBP', quality=85)
        
        thumb_name = f"thumb_{instance.image.name.split('/')[-1].split('.')[0]}.webp"
        instance.image_thumbnail.save(thumb_name, thumb_io, save=False)
```

### 3.5 Скрытие товаров «нет в наличии»

```python
# Backend: Фильтрация только доступных товаров
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    # По умолчанию показываем только доступные товары
    queryset = Product.objects.filter(is_available=True)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Опциональный параметр для показа всех товаров (для админов)
        show_all = self.request.query_params.get('show_all', 'false')
        if show_all.lower() == 'true' and self.request.user.is_staff:
            return Product.objects.all()
        
        return queryset
```

```html
<!-- Frontend: Визуальное отображение недоступного товара (если нужно показать) -->
<div class="menu-card {% if not product.is_available %}out-of-stock{% endif %}">
    {% if not product.is_available %}
    <div class="out-of-stock-overlay">
        <span>Нет в наличии</span>
    </div>
    {% endif %}
    <!-- ... -->
</div>
```

```css
/* CSS для недоступных товаров */
.menu-card.out-of-stock {
    opacity: 0.6;
    pointer-events: none;
}

.out-of-stock-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.9);
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
    color: #e74c3c;
}
```

---

## 4. Интеграция с WhatsApp-ботом

### 4.1 Единая база данных

```
┌─────────────────────────────────────────────────────────────┐
│                    ЕДИНАЯ БД (PostgreSQL/SQLite)            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                catalog_product                        │  │
│  │  id | name | price | currency | is_available | ...    │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│              ┌────────────┼────────────┐                   │
│              ▼            ▼            ▼                   │
│         ┌────────┐   ┌────────┐   ┌────────┐               │
│         │ Сайт   │   │WhatsApp│   │ Админ  │               │
│         │Каталог │   │  Бот   │   │Панель  │               │
│         └────────┘   └────────┘   └────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Формат данных для WhatsApp-бота

```python
# Сериализатор для WhatsApp
class ProductWhatsAppSerializer(serializers.ModelSerializer):
    formatted_price = serializers.CharField(read_only=True)
    whatsapp_text = serializers.CharField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'formatted_price', 'image',
            'short_description', 'whatsapp_text', 'is_available'
        ]
```

```python
# Property в модели Product для генерации текста WhatsApp
@property
def whatsapp_text(self):
    """Generate text for WhatsApp bot."""
    text = f"*{self.name}*\n"
    text += f"💰 {self.formatted_price}\n"
    if self.weight:
        text += f"📦 {self.weight}\n"
    text += f"\n{self.short_description or self.description[:200]}"
    return text
```

### 4.3 Передача выбранного товара в WhatsApp-бот

#### Вариант 1: Deep Link (рекомендуется)

```python
# В модели Product
def get_whatsapp_order_url(self):
    """Generate WhatsApp deep link for ordering."""
    from django.conf import settings
    from urllib.parse import quote
    
    message = f"Здравствуйте! Хочу заказать:\n{self.name}\nЦена: {self.formatted_price}"
    phone = settings.COMPANY_WHATSAPP.replace('+', '')
    
    return f"https://wa.me/{phone}?text={quote(message)}"
```

```html
<!-- Кнопка "Заказать в WhatsApp" на странице товара -->
<a href="{{ product.get_whatsapp_order_url }}" 
   class="whatsapp-order-btn"
   target="_blank"
   rel="noopener">
    <span class="whatsapp-icon">💬</span>
    Заказать в WhatsApp
</a>
```

#### Вариант 2: Передача через корзину

```javascript
// JavaScript: Формирование заказа из корзины для WhatsApp
function sendCartToWhatsApp() {
    const cart = getCart();  // Получаем корзину из localStorage
    const phone = document.body.dataset.whatsapp;
    
    let message = "Здравствуйте! Хочу заказать:\n\n";
    
    cart.items.forEach(item => {
        message += `• ${item.name} x${item.quantity} = ${item.price * item.quantity} сом\n`;
    });
    
    message += `\n💰 Итого: ${cart.total} сом`;
    
    const url = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
}
```

#### Вариант 3: Webhook для бота (автоматическая интеграция)

```python
# API эндпоинт для получения товара ботом
@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_for_bot(request, product_id):
    """
    GET /api/catalog/bot/product/{id}/
    
    Используется WhatsApp-ботом для получения актуальной информации о товаре.
    """
    try:
        product = Product.objects.get(id=product_id, is_available=True)
        return Response({
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'currency': product.currency,
            'formatted_price': product.formatted_price,
            'description': product.short_description,
            'image_url': request.build_absolute_uri(product.image.url) if product.image else None,
            'whatsapp_text': product.whatsapp_text,
            'is_available': product.is_available
        })
    except Product.DoesNotExist:
        return Response({'error': 'Товар не найден'}, status=404)
```

### 4.4 Синхронизация данных

```python
# signals.py — Уведомление бота об изменениях
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Product)
def product_updated(sender, instance, created, **kwargs):
    """
    При изменении товара:
    1. Инвалидируем кэш
    2. Оповещаем WhatsApp-бота (опционально)
    """
    # Инвалидация кэша
    cache.delete_many([
        'api_categories_list',
        'api_products_featured',
        'api_products_promotional',
        f'product_{instance.slug}',
        f'category_{instance.category.slug}_products',
    ])
    
    # Webhook для WhatsApp-бота (опционально)
    # notify_whatsapp_bot_about_change(instance)
```

---

## 5. Чек-лист соответствия ТЗ

### ✅ Соответствие каталога ТЗ — по пунктам

| № | Требование | Статус | Реализация |
|---|------------|--------|------------|
| **1** | **Единая БД для сайта и WhatsApp-бота** | ✅ | Модели `Product`, `Category` используются и сайтом, и ботом через API |
| **2.1** | Название товара | ✅ | Поле `name` (CharField, max_length=200) |
| **2.2** | Категория товара | ✅ | Поле `category` (ForeignKey → Category) |
| **2.3** | Описание товара | ✅ | Поля `description` (полное) и `short_description` (краткое) |
| **2.4** | Цена товара | ✅ | Поле `price` (DecimalField) |
| **2.5** | Валюта | ✅ | Поле `currency` (CharField с choices: KGS, RUB, USD, EUR, KZT) |
| **2.6** | Изображение | ✅ | Поле `image` (ImageField) + `images` (дополнительные фото) |
| **2.7** | Статус наличия | ✅ | Поле `is_available` (BooleanField) |
| **3.1** | Фильтрация по категориям | ✅ | Навигация с табами категорий, URL фильтр `?category=slug` |
| **3.2** | Карточки товаров | ✅ | Компонент `menu-card` с изображением, названием, ценой, кнопкой |
| **3.3** | Быстрая загрузка изображений | ✅ | `loading="lazy"`, thumbnails, WebP формат, preload |
| **4.1** | Быстрое обновление цен | ✅ | `updated_at` автообновление, API bulk-update, инвалидация кэша |
| **4.2** | Скрытие товаров «нет в наличии» | ✅ | Фильтр `is_available=True` в queryset по умолчанию |
| **4.3** | Передача товара в WhatsApp-бот | ✅ | Deep link `wa.me`, API endpoint `/whatsapp_card/`, `whatsapp_text` property |

### 📋 Дополнительные функции (сверх ТЗ)

| Функция | Статус | Описание |
|---------|--------|----------|
| Поиск товаров | ✅ | Полнотекстовый поиск с подсказками |
| Рекомендации похожих товаров | ✅ | API `/recommendations/similar/{id}/` |
| PDF-каталог для бота | ✅ | Модель `PDFCatalog` с генерацией |
| Синонимы для поиска | ✅ | Модель `SearchSynonym` для fuzzy search |
| Отслеживание популярности | ✅ | `view_count`, `purchase_count` |
| Кэширование | ✅ | Django Cache для списков категорий и популярных товаров |

---

## 📁 Структура файлов каталога

```
apps/catalog/
├── __init__.py
├── admin.py          # Админ-панель для управления товарами
├── apps.py
├── models.py         # Модели Product, Category, ProductImage, PDFCatalog
├── serializers.py    # REST сериализаторы для API
├── views.py          # API ViewSets (REST Framework)
├── frontend_views.py # Views для HTML страниц
├── urls.py           # API URLs (/api/catalog/...)
├── frontend_urls.py  # Frontend URLs (/menu/, /product/...)
├── search_service.py # Сервис поиска
├── search_views.py   # API поиска
├── signals.py        # Сигналы (кэш, уведомления)
├── tasks.py          # Celery задачи (PDF генерация)
└── migrations/

templates/catalog/
├── menu.html                # Страница каталога (меню)
├── catalog_list.html        # Альтернативный список товаров
├── catalog_list_menu.html   # Список в формате меню
└── product_detail_menu.html # Страница товара

static/
├── css/menu.css      # Стили каталога
├── css/cart.css      # Стили корзины
├── js/cart.js        # Логика корзины
└── js/search.js      # Автодополнение поиска
```

---

## 🚀 Быстрый старт

### Добавление нового товара

```python
# Через Django Admin или shell
from apps.catalog.models import Product, Category

category = Category.objects.get(slug='ovoschi')
product = Product.objects.create(
    name='Огурцы свежие',
    category=category,
    description='Хрустящие огурцы с грядки',
    price=80.00,
    currency='KGS',
    image='products/cucumbers.jpg',
    is_available=True,
    is_featured=True
)
```

### Массовое обновление цен

```python
# Через Django shell
from apps.catalog.models import Product

# Увеличить все цены на 10%
Product.objects.filter(is_available=True).update(
    price=F('price') * 1.1
)
```

### Скрыть товары без наличия

```python
Product.objects.filter(stock__lte=0).update(is_available=False)
```

---

*Документ составлен: 2026-01-28*
*Версия: 1.0*
