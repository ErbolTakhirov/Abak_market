# ==============================================
# ORDERS ADMIN CONFIGURATION
# ==============================================
"""
Admin interface for order management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline for order items."""
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_price', 'total_display')
    fields = ('product', 'product_name', 'quantity', 'price', 'total_display', 'notes')
    raw_id_fields = ('product',)
    
    def total_display(self, obj):
        if obj.pk:
            return f"{obj.total} ₽"
        return '-'
    total_display.short_description = _('Сумма')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin for orders with full management.
    """
    
    list_display = (
        'order_number', 'status_badge', 'customer_name', 'customer_phone',
        'items_count', 'total_display', 'source', 'created_at'
    )
    list_display_links = ('order_number', 'customer_name')
    list_filter = ('status', 'source', 'created_at', 'assigned_operator')
    search_fields = ('order_number', 'customer_name', 'customer_phone', 'customer_address')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = (
        'order_number', 'created_at', 'updated_at',
        'confirmed_at', 'completed_at', 'items_summary'
    )
    raw_id_fields = ('assigned_operator',)
    inlines = [OrderItemInline]
    
    fieldsets = (
        (_('Информация о заказе'), {
            'fields': ('order_number', 'status', 'source', 'assigned_operator')
        }),
        (_('Клиент'), {
            'fields': ('customer_name', 'customer_phone', 'customer_address', 'customer_notes')
        }),
        (_('Финансы'), {
            'fields': ('subtotal', 'delivery_fee', 'discount', 'total')
        }),
        (_('Позиции заказа'), {
            'fields': ('items_summary',),
            'classes': ('collapse',)
        }),
        (_('Служебное'), {
            'fields': ('admin_notes', 'created_at', 'updated_at', 'confirmed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'new': '#3498db',
            'confirmed': '#9b59b6',
            'processing': '#f39c12',
            'ready': '#1abc9c',
            'delivering': '#e67e22',
            'completed': '#27ae60',
            'cancelled': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Статус')
    status_badge.admin_order_field = 'status'
    
    def total_display(self, obj):
        """Display formatted total."""
        return format_html(
            '<span style="font-weight: bold; font-size: 14px;">{} ₽</span>',
            obj.total
        )
    total_display.short_description = _('Сумма')
    total_display.admin_order_field = 'total'
    
    def items_summary(self, obj):
        """Display items summary."""
        items = obj.items.all()
        if not items:
            return _('Нет позиций')
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f5f5f5;"><th>Товар</th><th>Кол-во</th><th>Цена</th><th>Сумма</th></tr>'
        
        for item in items:
            html += f'<tr><td>{item.product_name}</td><td>{item.quantity}</td>'
            html += f'<td>{item.price} ₽</td><td>{item.total} ₽</td></tr>'
        
        html += f'<tr style="font-weight: bold; background: #e8f5e9;">'
        html += f'<td colspan="3">Итого:</td><td>{obj.total} ₽</td></tr>'
        html += '</table>'
        
        return format_html(html)
    items_summary.short_description = _('Позиции')
    
    actions = ['mark_confirmed', 'mark_processing', 'mark_completed', 'mark_cancelled']
    
    @admin.action(description=_('Подтвердить заказы'))
    def mark_confirmed(self, request, queryset):
        for order in queryset.filter(status=Order.Status.NEW):
            order.confirm()
        self.message_user(request, _('Заказы подтверждены'))
    
    @admin.action(description=_('В обработку'))
    def mark_processing(self, request, queryset):
        queryset.update(status=Order.Status.PROCESSING)
        self.message_user(request, _('Статус изменён на "В обработке"'))
    
    @admin.action(description=_('Выполнить заказы'))
    def mark_completed(self, request, queryset):
        for order in queryset.exclude(status=Order.Status.CANCELLED):
            order.complete()
        self.message_user(request, _('Заказы выполнены'))
    
    @admin.action(description=_('Отменить заказы'))
    def mark_cancelled(self, request, queryset):
        for order in queryset.exclude(status=Order.Status.COMPLETED):
            order.cancel('Отменено администратором')
        self.message_user(request, _('Заказы отменены'))


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Separate admin for order items (rarely used directly).
    """
    list_display = ('order', 'product_name', 'quantity', 'price', 'total')
    list_filter = ('order__status',)
    search_fields = ('product_name', 'order__order_number')
    raw_id_fields = ('order', 'product')
