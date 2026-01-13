# ==============================================
# DIALOG MODELS
# ==============================================
"""
Models for storing WhatsApp conversation history.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Dialog(models.Model):
    """
    Conversation/dialog with a customer.
    """
    
    customer_phone = models.CharField(
        _('Телефон клиента'),
        max_length=20,
        unique=True,
        db_index=True
    )
    customer_name = models.CharField(
        _('Имя клиента'),
        max_length=200,
        blank=True,
        default='Клиент'
    )
    
    # Status
    is_active = models.BooleanField(
        _('Активен'),
        default=True
    )
    is_assigned = models.BooleanField(
        _('Назначен оператору'),
        default=False
    )
    
    # Tags for filtering
    tags = models.CharField(
        _('Теги'),
        max_length=500,
        blank=True,
        help_text=_('Через запятую')
    )
    
    # Notes
    notes = models.TextField(
        _('Заметки'),
        blank=True
    )
    
    # Stats
    messages_count = models.PositiveIntegerField(
        _('Количество сообщений'),
        default=0
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        _('Создан'),
        auto_now_add=True
    )
    last_message_at = models.DateTimeField(
        _('Последнее сообщение'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Диалог')
        verbose_name_plural = _('Диалоги')
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['customer_phone']),
            models.Index(fields=['is_active', 'last_message_at']),
        ]
    
    def __str__(self):
        return f"Диалог с {self.customer_name} ({self.customer_phone})"
    
    def get_recent_messages(self, limit: int = 10):
        """Get recent messages in dialog."""
        return self.messages.order_by('-created_at')[:limit]
    
    def update_stats(self):
        """Update dialog statistics."""
        self.messages_count = self.messages.count()
        last_msg = self.messages.order_by('-created_at').first()
        if last_msg:
            self.last_message_at = last_msg.created_at
        self.save(update_fields=['messages_count', 'last_message_at'])


class Message(models.Model):
    """
    Individual message in a dialog.
    """
    
    class Direction(models.TextChoices):
        CUSTOMER = 'customer', _('От клиента')
        BOT = 'bot', _('От бота')
        OPERATOR = 'operator', _('От оператора')
    
    class MessageType(models.TextChoices):
        TEXT = 'text', _('Текст')
        IMAGE = 'image', _('Изображение')
        AUDIO = 'audio', _('Аудио')
        DOCUMENT = 'document', _('Документ')
        INTERACTIVE = 'interactive', _('Интерактивное')
        TEMPLATE = 'template', _('Шаблон')
    
    dialog = models.ForeignKey(
        Dialog,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Диалог')
    )
    
    # WhatsApp API fields
    whatsapp_message_id = models.CharField(
        _('WhatsApp ID'),
        max_length=100,
        blank=True,
        db_index=True
    )
    
    # Message content
    direction = models.CharField(
        _('Направление'),
        max_length=10,
        choices=Direction.choices
    )
    message_type = models.CharField(
        _('Тип'),
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )
    content = models.TextField(
        _('Содержимое')
    )
    
    # For voice messages
    transcription = models.TextField(
        _('Расшифровка'),
        blank=True,
        help_text=_('Расшифровка голосового сообщения')
    )
    
    # Media
    media_url = models.URLField(
        _('URL медиа'),
        blank=True
    )
    media_file = models.FileField(
        _('Медиа файл'),
        upload_to='dialogs/media/',
        blank=True
    )
    
    # Status
    delivery_status = models.CharField(
        _('Статус доставки'),
        max_length=20,
        blank=True,
        help_text=_('sent, delivered, read, failed')
    )
    
    # Raw data for debugging
    raw_data = models.JSONField(
        _('Сырые данные'),
        default=dict,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        _('Создано'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['dialog', 'created_at']),
            models.Index(fields=['whatsapp_message_id']),
        ]
    
    def __str__(self):
        return f"[{self.direction}] {self.content[:50]}..."
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update dialog stats
        self.dialog.update_stats()
