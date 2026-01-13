# ==============================================
# PAYMENT MODELS
# ==============================================
"""
Payment method and requisites models.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMethod(models.Model):
    """
    Payment method with requisites for customers.
    """
    
    class MethodType(models.TextChoices):
        CARD = 'card', _('Банковская карта')
        CASH = 'cash', _('Наличные')
        BANK_TRANSFER = 'transfer', _('Банковский перевод')
        QR_CODE = 'qr', _('QR-код')
        ONLINE = 'online', _('Онлайн-оплата')
    
    name = models.CharField(
        _('Название'),
        max_length=100
    )
    method_type = models.CharField(
        _('Тип'),
        max_length=20,
        choices=MethodType.choices,
        default=MethodType.CARD
    )
    details = models.TextField(
        _('Реквизиты'),
        help_text=_('Номер карты, счёт, инструкции')
    )
    instructions = models.TextField(
        _('Инструкции для клиента'),
        blank=True
    )
    
    # For QR payments
    qr_image = models.ImageField(
        _('QR-код'),
        upload_to='payments/qr/',
        blank=True,
        null=True
    )
    
    # Ordering and visibility
    order = models.PositiveIntegerField(
        _('Порядок'),
        default=0
    )
    is_active = models.BooleanField(
        _('Активен'),
        default=True
    )
    
    # For WhatsApp bot
    show_in_bot = models.BooleanField(
        _('Показывать в боте'),
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
        verbose_name = _('Способ оплаты')
        verbose_name_plural = _('Способы оплаты')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def whatsapp_text(self):
        """Format for WhatsApp message."""
        text = f"*{self.name}*\n{self.details}"
        if self.instructions:
            text += f"\n\n_{self.instructions}_"
        return text


class PaymentRequisite(models.Model):
    """
    Individual payment requisite (card number, account, etc.).
    """
    
    method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.CASCADE,
        related_name='requisites',
        verbose_name=_('Способ оплаты')
    )
    name = models.CharField(
        _('Название'),
        max_length=100,
        help_text=_('Например: Карта Сбербанк')
    )
    value = models.CharField(
        _('Значение'),
        max_length=200,
        help_text=_('Номер карты, счёт и т.д.')
    )
    holder_name = models.CharField(
        _('Имя получателя'),
        max_length=200,
        blank=True
    )
    is_primary = models.BooleanField(
        _('Основной'),
        default=False
    )
    is_active = models.BooleanField(
        _('Активен'),
        default=True
    )
    
    class Meta:
        verbose_name = _('Реквизит')
        verbose_name_plural = _('Реквизиты')
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name}: {self.value}"
