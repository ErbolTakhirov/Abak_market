# ==============================================
# CATALOG MODELS
# ==============================================
"""
Product and Category models for the grocery store.
Shared between website and WhatsApp bot.
"""

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.utils import slugify_ru, get_product_image_path, get_category_image_path


class Category(models.Model):
    """
    Product category model.
    """
    
    class CategoryType(models.TextChoices):
        PRODUCTS = 'products', _('Продукты')
        DISHES = 'dishes', _('Готовые блюда')
        PROMOTIONS = 'promotions', _('Акции')
    
    name = models.CharField(
        _('Название'),
        max_length=100
    )
    slug = models.SlugField(
        _('URL'),
        max_length=120,
        unique=True,
        blank=True
    )
    description = models.TextField(
        _('Описание'),
        blank=True
    )
    category_type = models.CharField(
        _('Тип категории'),
        max_length=20,
        choices=CategoryType.choices,
        default=CategoryType.PRODUCTS
    )
    image = models.ImageField(
        _('Изображение'),
        upload_to=get_category_image_path,
        blank=True,
        null=True
    )
    icon = models.CharField(
        _('Иконка (emoji)'),
        max_length=10,
        blank=True,
        default='🛒'
    )
    
    # Ordering and visibility
    order = models.PositiveIntegerField(
        _('Порядок'),
        default=0
    )
    is_active = models.BooleanField(
        _('Активна'),
        default=True
    )
    show_on_home = models.BooleanField(
        _('Показывать на главной'),
        default=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        _('Создана'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Обновлена'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_ru(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('catalog:category', kwargs={'slug': self.slug})
    
    @property
    def products_count(self):
        """Number of available products in category."""
        return self.products.filter(is_available=True).count()


class Product(models.Model):
    """
    Product/Dish model for the grocery store.
    """
    
    class Currency(models.TextChoices):
        RUB = 'RUB', '₽'
        USD = 'USD', '$'
        EUR = 'EUR', '€'
        KZT = 'KZT', '₸'
    
    # Basic info
    name = models.CharField(
        _('Название'),
        max_length=200
    )
    slug = models.SlugField(
        _('URL'),
        max_length=220,
        unique=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Категория')
    )
    description = models.TextField(
        _('Описание')
    )
    short_description = models.CharField(
        _('Краткое описание'),
        max_length=300,
        blank=True,
        help_text=_('Для карточек товаров и WhatsApp')
    )
    
    # Pricing
    price = models.DecimalField(
        _('Цена'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    old_price = models.DecimalField(
        _('Старая цена'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Для отображения скидки')
    )
    currency = models.CharField(
        _('Валюта'),
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB
    )
    
    # Unit and quantity
    unit = models.CharField(
        _('Единица измерения'),
        max_length=20,
        default='шт',
        help_text=_('шт, кг, л, порция и т.д.')
    )
    min_quantity = models.PositiveIntegerField(
        _('Минимальное количество'),
        default=1
    )
    
    # Images
    image = models.ImageField(
        _('Основное изображение'),
        upload_to=get_product_image_path
    )
    image_thumbnail = models.ImageField(
        _('Миниатюра'),
        upload_to=get_product_image_path,
        blank=True,
        null=True
    )
    
    # Status and visibility
    is_available = models.BooleanField(
        _('В наличии'),
        default=True
    )
    is_featured = models.BooleanField(
        _('Популярный'),
        default=False,
        help_text=_('Показывать на главной странице')
    )
    is_promotional = models.BooleanField(
        _('Акционный'),
        default=False,
        help_text=_('Товар по акции')
    )
    is_new = models.BooleanField(
        _('Новинка'),
        default=False
    )
    
    # Additional info
    weight = models.CharField(
        _('Вес/Объём'),
        max_length=50,
        blank=True,
        help_text=_('Например: 500г, 1л')
    )
    calories = models.PositiveIntegerField(
        _('Калорийность'),
        null=True,
        blank=True,
        help_text=_('ккал на 100г')
    )
    ingredients = models.TextField(
        _('Состав'),
        blank=True
    )
    
    # SEO
    meta_title = models.CharField(
        _('SEO заголовок'),
        max_length=200,
        blank=True
    )
    meta_description = models.CharField(
        _('SEO описание'),
        max_length=300,
        blank=True
    )
    
    # Ordering
    order = models.PositiveIntegerField(
        _('Порядок'),
        default=0
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        _('Создан'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Обновлён'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['is_available', 'is_featured']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_ru(self.name)
        if not self.short_description and self.description:
            self.short_description = self.description[:297] + '...' if len(self.description) > 300 else self.description
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('catalog:product', kwargs={'slug': self.slug})
    
    @property
    def discount_percent(self):
        """Calculate discount percentage."""
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0
    
    @property
    def formatted_price(self):
        """Return formatted price string."""
        from apps.core.utils import format_price
        return format_price(float(self.price), self.currency)
    
    @property
    def whatsapp_text(self):
        """Generate text for WhatsApp bot."""
        text = f"*{self.name}*\n"
        text += f"💰 {self.formatted_price}\n"
        if self.weight:
            text += f"📦 {self.weight}\n"
        text += f"\n{self.short_description or self.description[:200]}"
        return text
    
    def get_whatsapp_order_url(self):
        """Generate WhatsApp deep link for ordering."""
        from django.conf import settings
        from urllib.parse import quote
        
        message = f"Здравствуйте! Хочу заказать:\n{self.name}\nЦена: {self.formatted_price}"
        phone = settings.COMPANY_WHATSAPP.replace('+', '')
        
        return f"https://wa.me/{phone}?text={quote(message)}"


class ProductImage(models.Model):
    """
    Additional product images.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Товар')
    )
    image = models.ImageField(
        _('Изображение'),
        upload_to=get_product_image_path
    )
    alt_text = models.CharField(
        _('Alt текст'),
        max_length=200,
        blank=True
    )
    order = models.PositiveIntegerField(
        _('Порядок'),
        default=0
    )
    
    class Meta:
        verbose_name = _('Изображение товара')
        verbose_name_plural = _('Изображения товаров')
        ordering = ['order']
    
    def __str__(self):
        return f"Изображение для {self.product.name}"


class PDFCatalog(models.Model):
    """
    PDF catalog files for WhatsApp bot.
    """
    
    name = models.CharField(
        _('Название'),
        max_length=100
    )
    file = models.FileField(
        _('PDF файл'),
        upload_to='catalogs/'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pdf_catalogs',
        verbose_name=_('Категория'),
        help_text=_('Оставьте пустым для общего каталога')
    )
    is_active = models.BooleanField(
        _('Активен'),
        default=True
    )
    created_at = models.DateTimeField(
        _('Создан'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Обновлён'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('PDF каталог')
        verbose_name_plural = _('PDF каталоги')
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_latest(cls, category=None):
        """Get latest active catalog."""
        queryset = cls.objects.filter(is_active=True)
        if category:
            queryset = queryset.filter(category=category)
        else:
            queryset = queryset.filter(category__isnull=True)
        return queryset.first()
