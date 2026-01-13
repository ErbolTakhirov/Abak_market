# ==============================================
# USER ADMIN CONFIGURATION
# ==============================================
"""
Admin interface for user and operator management.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import User, OperatorAssignment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model.
    """
    
    list_display = (
        'email', 'get_full_name', 'role', 'is_online_display',
        'is_active', 'is_staff', 'date_joined'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_online', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_activity')
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Личная информация'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Роль и права'), {
            'fields': ('role', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Статус оператора'), {
            'fields': ('is_online', 'telegram_id', 'notify_on_new_order', 'notify_on_operator_request')
        }),
        (_('Важные даты'), {
            'fields': ('date_joined', 'last_activity')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_active'),
        }),
    )
    
    def is_online_display(self, obj):
        """Display online status with color."""
        if obj.is_online:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● Онлайн</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">○ Офлайн</span>'
        )
    is_online_display.short_description = _('Статус')
    
    actions = ['set_online', 'set_offline']
    
    @admin.action(description=_('Перевести в онлайн'))
    def set_online(self, request, queryset):
        queryset.update(is_online=True)
        self.message_user(request, _('Операторы переведены в онлайн'))
    
    @admin.action(description=_('Перевести в офлайн'))
    def set_offline(self, request, queryset):
        queryset.update(is_online=False)
        self.message_user(request, _('Операторы переведены в офлайн'))


@admin.register(OperatorAssignment)
class OperatorAssignmentAdmin(admin.ModelAdmin):
    """
    Admin for operator assignments.
    """
    
    list_display = (
        'operator', 'customer_phone', 'is_active',
        'assigned_at', 'closed_at'
    )
    list_filter = ('is_active', 'assigned_at', 'operator')
    search_fields = ('customer_phone', 'operator__email', 'operator__first_name')
    ordering = ('-assigned_at',)
    readonly_fields = ('assigned_at',)
    raw_id_fields = ('operator',)
    
    actions = ['close_assignments']
    
    @admin.action(description=_('Закрыть выбранные назначения'))
    def close_assignments(self, request, queryset):
        from django.utils import timezone
        queryset.filter(is_active=True).update(
            is_active=False,
            closed_at=timezone.now()
        )
        self.message_user(request, _('Назначения закрыты'))
