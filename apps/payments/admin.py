# ==============================================
# PAYMENTS ADMIN
# ==============================================

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import PaymentMethod, PaymentRequisite


class PaymentRequisiteInline(admin.TabularInline):
    model = PaymentRequisite
    extra = 1
    fields = ('name', 'value', 'holder_name', 'is_primary', 'is_active')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'method_type', 'is_active', 'show_in_bot', 'order')
    list_filter = ('method_type', 'is_active', 'show_in_bot')
    search_fields = ('name', 'details')
    ordering = ('order', 'name')
    list_editable = ('is_active', 'show_in_bot', 'order')
    inlines = [PaymentRequisiteInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'method_type', 'details', 'instructions')
        }),
        (_('QR-код'), {
            'fields': ('qr_image',),
            'classes': ('collapse',)
        }),
        (_('Настройки'), {
            'fields': ('order', 'is_active', 'show_in_bot')
        }),
    )
    
    def qr_preview(self, obj):
        if obj.qr_image:
            return format_html(
                '<img src="{}" width="100" />',
                obj.qr_image.url
            )
        return '-'
    qr_preview.short_description = _('QR')


@admin.register(PaymentRequisite)
class PaymentRequisiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'value', 'is_primary', 'is_active')
    list_filter = ('method', 'is_active', 'is_primary')
    search_fields = ('name', 'value', 'holder_name')
