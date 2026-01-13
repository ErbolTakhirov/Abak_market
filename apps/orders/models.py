# ==============================================
# ORDER MODELS
# ==============================================
"""
Order and order item models for tracking customer requests.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.utils import generate_short_id


class Order(models.Model):
    """
    Customer order model.
    Orders can come from website or WhatsApp bot.
    """
    
    class Status(models.TextChoices):
        NEW = 'new', _('Новый')
        CONFIRMED = 'confirmed', _('Подтверждён')
        PROCESSING = 'processing', _('В обработке')
        READY = 'ready', _('Готов')
        DELIVERING = 'delivering', _('Доставляется')
        COMPLETED = 'completed', _('Выполнен')
        CANCELLED = 'cancelled', _('Отменён')
    
    class Source(models.TextChoices):
        WEBSITE = 'website', _('Сайт')
        WHATSAPP = 'whatsapp', _('WhatsApp')
        PHONE = 'phone', _('Телефон')
    
    # Order identification
    order_number = models.CharField(
        _('Номер заказа'),
        max_length=20,
        unique=True,
        editable=False
    )
    
    # Customer info
    customer_name = models.CharField(
        _('Имя клиента'),
        max_length=200
    )
    customer_phone = models.CharField(
        _('Телефон'),
        max_length=20,
        db_index=True
    )
    customer_address = models.TextField(
        _('Адрес доставки'),
        blank=True
    )
    
    # Order details
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True
    )
    source = models.CharField(
        _('Источник'),
        max_length=20,
        choices=Source.choices,
        default=Source.WHATSAPP
    )
    
    # Financial
    subtotal = models.DecimalField(
        _('Сумма товаров'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    delivery_fee = models.DecimalField(
        _('Стоимость доставки'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    discount = models.DecimalField(
        _('Скидка'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        _('Итого'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Notes
    customer_notes = models.TextField(
        _('Комментарий клиента'),
        blank=True
    )
    admin_notes = models.TextField(
        _('Заметки администратора'),
        blank=True
    )
    
    # Operator
    assigned_operator = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        verbose_name=_('Оператор')
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
    confirmed_at = models.DateTimeField(
        _('Подтверждён'),
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(
        _('Выполнен'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['customer_phone']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"Заказ #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        
        # Calculate total
        self.total = self.subtotal + self.delivery_fee - self.discount
        
        super().save(*args, **kwargs)
    
    def _generate_order_number(self):
        """Generate unique order number."""
        from django.utils import timezone
        prefix = timezone.now().strftime('%y%m')
        suffix = generate_short_id(6)
        return f"{prefix}-{suffix}"
    
    @property
    def items_count(self):
        """Total number of items in order."""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    def calculate_totals(self):
        """Recalculate order totals from items."""
        from django.db.models import Sum, F
        
        result = self.items.aggregate(
            subtotal=Sum(F('price') * F('quantity'))
        )
        self.subtotal = result['subtotal'] or 0
        self.total = self.subtotal + self.delivery_fee - self.discount
        self.save(update_fields=['subtotal', 'total'])
    
    def confirm(self):
        """Confirm order."""
        from django.utils import timezone
        self.status = self.Status.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at', 'updated_at'])
    
    def complete(self):
        """Mark order as completed."""
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])
    
    def cancel(self, reason=''):
        """Cancel order."""
        self.status = self.Status.CANCELLED
        if reason:
            self.admin_notes += f"\nПричина отмены: {reason}"
        self.save(update_fields=['status', 'admin_notes', 'updated_at'])


class OrderItem(models.Model):
    """
    Individual item in an order.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Заказ')
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name=_('Товар')
    )
    
    # Snapshot of product data at order time
    product_name = models.CharField(
        _('Название товара'),
        max_length=200
    )
    product_price = models.DecimalField(
        _('Цена товара'),
        max_digits=10,
        decimal_places=2
    )
    
    # Order item specific
    quantity = models.PositiveIntegerField(
        _('Количество'),
        default=1
    )
    price = models.DecimalField(
        _('Цена'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Может отличаться от цены товара (скидки)')
    )
    notes = models.CharField(
        _('Примечание'),
        max_length=200,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Позиция заказа')
        verbose_name_plural = _('Позиции заказа')
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Snapshot product data
        if self.product and not self.product_name:
            self.product_name = self.product.name
            self.product_price = self.product.price
        
        if not self.price:
            self.price = self.product_price
        
        super().save(*args, **kwargs)
    
    @property
    def total(self):
        """Total price for this item."""
        return self.price * self.quantity
