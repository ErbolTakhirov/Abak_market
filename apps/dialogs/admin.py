# ==============================================
# DIALOGS ADMIN
# ==============================================

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Dialog, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('direction', 'message_type', 'content_preview', 'created_at')
    fields = ('direction', 'message_type', 'content_preview', 'created_at')
    ordering = ('-created_at',)
    max_num = 20
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = _('Сообщение')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = (
        'customer_name', 'customer_phone', 'messages_count',
        'is_active', 'is_assigned', 'last_message_display'
    )
    list_filter = ('is_active', 'is_assigned', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'tags', 'notes')
    ordering = ('-last_message_at',)
    readonly_fields = ('messages_count', 'created_at', 'last_message_at')
    inlines = [MessageInline]
    
    fieldsets = (
        (None, {
            'fields': ('customer_name', 'customer_phone')
        }),
        (_('Статус'), {
            'fields': ('is_active', 'is_assigned')
        }),
        (_('Дополнительно'), {
            'fields': ('tags', 'notes')
        }),
        (_('Статистика'), {
            'fields': ('messages_count', 'created_at', 'last_message_at')
        }),
    )
    
    def last_message_display(self, obj):
        if obj.last_message_at:
            diff = timezone.now() - obj.last_message_at
            if diff.days == 0:
                hours = diff.seconds // 3600
                if hours == 0:
                    mins = diff.seconds // 60
                    return f"{mins} мин назад"
                return f"{hours} ч назад"
            return f"{diff.days} дн назад"
        return '-'
    last_message_display.short_description = _('Последнее')
    
    actions = ['mark_inactive', 'mark_active']
    
    @admin.action(description=_('Деактивировать'))
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
    
    @admin.action(description=_('Активировать'))
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'dialog', 'direction_badge', 'message_type',
        'content_preview', 'delivery_status', 'created_at'
    )
    list_filter = ('direction', 'message_type', 'created_at')
    search_fields = ('content', 'dialog__customer_phone')
    ordering = ('-created_at',)
    readonly_fields = ('whatsapp_message_id', 'created_at', 'raw_data')
    raw_id_fields = ('dialog',)
    
    def direction_badge(self, obj):
        colors = {
            'customer': '#3498db',
            'bot': '#27ae60',
            'operator': '#9b59b6'
        }
        color = colors.get(obj.direction, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_direction_display()
        )
    direction_badge.short_description = _('Направление')
    
    def content_preview(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    content_preview.short_description = _('Сообщение')
