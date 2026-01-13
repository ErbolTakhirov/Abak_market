# ==============================================
# WHATSAPP MESSAGE HANDLER
# ==============================================
"""
Main message handler for WhatsApp bot.
Routes messages to appropriate handlers.
"""

import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache

from apps.dialogs.models import Dialog, Message
from apps.users.models import OperatorAssignment
from apps.core.utils import normalize_phone_for_whatsapp, parse_menu_command
from ..services.whatsapp_api import WhatsAppAPI

logger = logging.getLogger(__name__)


class MessageHandler:
    """
    Main handler for incoming WhatsApp messages.
    """
    
    def __init__(self):
        self.api = WhatsAppAPI()
    
    def handle(self, message: dict, contact: dict, metadata: dict):
        """
        Handle incoming message.
        
        Args:
            message: Message data from webhook
            contact: Contact info
            metadata: Webhook metadata
        """
        message_type = message.get('type')
        sender_phone = message.get('from')
        message_id = message.get('id')
        timestamp = message.get('timestamp')
        
        # Get or create dialog
        dialog = self._get_or_create_dialog(sender_phone, contact)
        
        # Mark message as read
        try:
            self.api.mark_as_read(message_id)
        except Exception as e:
            logger.warning(f"Failed to mark message as read: {e}")
        
        # Check if assigned to operator
        operator = OperatorAssignment.get_active_operator(sender_phone)
        if operator:
            # Forward to operator (don't auto-respond)
            self._save_message(dialog, message, 'customer')
            self._notify_operator(dialog, message, operator)
            return
        
        # Dispatch based on message type
        if message_type == 'text':
            self._handle_text_message(dialog, message)
        elif message_type == 'audio':
            self._handle_voice_message(dialog, message)
        elif message_type == 'image':
            self._handle_image_message(dialog, message)
        elif message_type == 'interactive':
            self._handle_interactive_response(dialog, message)
        else:
            # Unknown type - save and respond with menu
            self._save_message(dialog, message, 'customer')
            self._send_welcome_menu(sender_phone)
    
    def _get_or_create_dialog(self, phone: str, contact: dict) -> Dialog:
        """Get or create dialog for customer."""
        dialog, created = Dialog.objects.get_or_create(
            customer_phone=phone,
            defaults={
                'customer_name': contact.get('profile', {}).get('name', 'Клиент'),
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"Created new dialog for {phone}")
        
        # Update last activity
        from django.utils import timezone
        dialog.last_message_at = timezone.now()
        dialog.save(update_fields=['last_message_at'])
        
        return dialog
    
    def _save_message(self, dialog: Dialog, message: dict, direction: str) -> Message:
        """Save message to database."""
        return Message.objects.create(
            dialog=dialog,
            whatsapp_message_id=message.get('id', ''),
            direction=direction,
            message_type=message.get('type', 'text'),
            content=self._extract_content(message),
            raw_data=message
        )
    
    def _extract_content(self, message: dict) -> str:
        """Extract text content from message."""
        msg_type = message.get('type')
        
        if msg_type == 'text':
            return message.get('text', {}).get('body', '')
        elif msg_type == 'interactive':
            interactive = message.get('interactive', {})
            if 'button_reply' in interactive:
                return interactive['button_reply'].get('title', '')
            if 'list_reply' in interactive:
                return interactive['list_reply'].get('title', '')
        elif msg_type == 'audio':
            return '[Голосовое сообщение]'
        elif msg_type == 'image':
            return message.get('image', {}).get('caption', '[Изображение]')
        
        return ''
    
    def _handle_text_message(self, dialog: Dialog, message: dict):
        """Handle text message."""
        text = message.get('text', {}).get('body', '')
        phone = message.get('from')
        
        # Save message
        self._save_message(dialog, message, 'customer')
        
        # Check for commands
        command = parse_menu_command(text)
        
        if command == 'menu':
            self._send_welcome_menu(phone)
        elif command == 'catalog':
            self._send_catalog_menu(phone)
        elif command == 'payment':
            self._send_payment_info(phone)
        elif command == 'operator':
            self._request_operator(dialog, phone)
        else:
            # Check if it's first message (greet new users)
            if dialog.messages.count() <= 1:
                self._send_welcome_menu(phone)
            else:
                # Try to understand intent or offer menu
                self._send_help_message(phone)
    
    def _handle_voice_message(self, dialog: Dialog, message: dict):
        """Handle voice message - queue for processing."""
        phone = message.get('from')
        audio_data = message.get('audio', {})
        
        # Save message
        saved_msg = self._save_message(dialog, message, 'customer')
        
        # Acknowledge receipt
        self.api.send_text_message(
            to=phone,
            text="🎤 Получил ваше голосовое сообщение. Обрабатываю..."
        )
        
        # Queue for async processing
        from ..tasks import process_voice_message
        process_voice_message.delay(
            dialog_id=dialog.id,
            message_id=saved_msg.id,
            audio_id=audio_data.get('id'),
            phone=phone
        )
    
    def _handle_image_message(self, dialog: Dialog, message: dict):
        """Handle image message."""
        phone = message.get('from')
        
        # Save message
        self._save_message(dialog, message, 'customer')
        
        # Acknowledge and offer help
        self.api.send_text_message(
            to=phone,
            text="📷 Спасибо за изображение! Если вам нужна помощь, нажмите кнопку ниже."
        )
        
        self._send_help_buttons(phone)
    
    def _handle_interactive_response(self, dialog: Dialog, message: dict):
        """Handle interactive button/list response."""
        phone = message.get('from')
        interactive = message.get('interactive', {})
        
        # Get button or list selection
        button_reply = interactive.get('button_reply', {})
        list_reply = interactive.get('list_reply', {})
        
        button_id = button_reply.get('id') or list_reply.get('id', '')
        
        # Save message
        self._save_message(dialog, message, 'customer')
        
        # Route based on button ID
        if button_id == 'btn_catalog':
            self._send_catalog_menu(phone)
        elif button_id == 'btn_payment':
            self._send_payment_info(phone)
        elif button_id == 'btn_operator':
            self._request_operator(dialog, phone)
        elif button_id == 'btn_menu':
            self._send_welcome_menu(phone)
        elif button_id.startswith('cat_'):
            category_id = button_id.replace('cat_', '')
            self._send_category_products(phone, category_id)
        elif button_id == 'btn_pdf':
            self._send_pdf_catalog(phone)
        else:
            self._send_welcome_menu(phone)
    
    def _send_welcome_menu(self, phone: str):
        """Send welcome message with main menu."""
        welcome_text = f"""
👋 *Добро пожаловать в {settings.COMPANY_NAME}!*

{settings.COMPANY_DESCRIPTION}

Выберите действие из меню ниже:
        """.strip()
        
        buttons = [
            {'id': 'btn_catalog', 'title': '📋 Каталог'},
            {'id': 'btn_payment', 'title': '💳 Оплата'},
            {'id': 'btn_operator', 'title': '👨‍💼 Оператор'}
        ]
        
        response = self.api.send_interactive_buttons(
            to=phone,
            body_text=welcome_text,
            buttons=buttons,
            footer_text='Напишите "Меню" для повтора'
        )
        
        self._save_bot_message(phone, welcome_text, response)
    
    def _send_catalog_menu(self, phone: str):
        """Send catalog category menu."""
        from apps.catalog.models import Category
        
        categories = Category.objects.filter(is_active=True).order_by('order')[:10]
        
        if not categories:
            self.api.send_text_message(phone, "Каталог пока пуст. Попробуйте позже.")
            return
        
        # Build list sections
        sections = [{
            'title': 'Категории',
            'rows': [
                {
                    'id': f'cat_{cat.id}',
                    'title': f'{cat.icon} {cat.name}'[:24],
                    'description': f'{cat.products_count} товаров'
                }
                for cat in categories
            ]
        }]
        
        # Add PDF option
        sections[0]['rows'].append({
            'id': 'btn_pdf',
            'title': '📄 PDF каталог',
            'description': 'Скачать полный каталог'
        })
        
        body_text = "📋 *Наш каталог*\n\nВыберите категорию товаров:"
        
        response = self.api.send_interactive_list(
            to=phone,
            body_text=body_text,
            button_text='Выбрать',
            sections=sections
        )
        
        self._save_bot_message(phone, body_text, response)
    
    def _send_category_products(self, phone: str, category_id: str):
        """Send products from category."""
        from apps.catalog.models import Category, Product
        
        try:
            category = Category.objects.get(id=category_id)
            products = Product.objects.filter(
                category=category,
                is_available=True
            )[:5]
            
            if not products:
                self.api.send_text_message(
                    phone,
                    f"В категории {category.name} пока нет товаров."
                )
                return
            
            # Send category header
            self.api.send_text_message(
                phone,
                f"{category.icon} *{category.name}*\n\n{category.description or 'Товары категории:'}"
            )
            
            # Send product cards
            for product in products:
                self._send_product_card(phone, product)
            
            # Send navigation buttons
            self._send_catalog_navigation(phone)
            
        except Category.DoesNotExist:
            self._send_catalog_menu(phone)
    
    def _send_product_card(self, phone: str, product):
        """Send product card with image and info."""
        # Send image if available
        if product.image:
            try:
                image_url = product.image.url
                if not image_url.startswith('http'):
                    # Build absolute URL (would need request context in production)
                    image_url = f"https://yourdomain.com{image_url}"
                
                self.api.send_image(
                    to=phone,
                    image_url=image_url,
                    caption=product.whatsapp_text
                )
            except Exception as e:
                logger.warning(f"Failed to send product image: {e}")
                # Fallback to text
                self.api.send_text_message(phone, product.whatsapp_text)
        else:
            self.api.send_text_message(phone, product.whatsapp_text)
    
    def _send_catalog_navigation(self, phone: str):
        """Send navigation buttons after product list."""
        buttons = [
            {'id': 'btn_catalog', 'title': '📋 Другие категории'},
            {'id': 'btn_operator', 'title': '🛒 Заказать'},
            {'id': 'btn_menu', 'title': '🏠 Меню'}
        ]
        
        self.api.send_interactive_buttons(
            to=phone,
            body_text="Что делаем дальше?",
            buttons=buttons
        )
    
    def _send_payment_info(self, phone: str):
        """Send payment information."""
        from apps.payments.models import PaymentMethod
        
        methods = PaymentMethod.objects.filter(is_active=True)
        
        text = "💳 *Способы оплаты*\n\n"
        
        if methods:
            for method in methods:
                text += f"*{method.name}*\n{method.details}\n\n"
        else:
            text += "Оплата наличными при получении или переводом на карту.\n\n"
        
        text += f"📞 Для уточнения: {settings.COMPANY_PHONE}"
        
        response = self.api.send_text_message(phone, text)
        self._save_bot_message(phone, text, response)
        
        # Send menu buttons
        self._send_help_buttons(phone)
    
    def _send_pdf_catalog(self, phone: str):
        """Send PDF catalog."""
        from ..tasks import send_pdf_catalog
        
        self.api.send_text_message(
            phone,
            "📄 Отправляю PDF каталог..."
        )
        
        # Queue PDF sending
        send_pdf_catalog.delay(phone)
    
    def _request_operator(self, dialog: Dialog, phone: str):
        """Request connection to operator."""
        from apps.users.models import User, OperatorAssignment
        
        # Assign operator
        assignment = OperatorAssignment.assign_operator(phone)
        
        if assignment:
            # Notify customer
            self.api.send_text_message(
                phone,
                f"👨‍💼 Оператор *{assignment.operator.get_short_name()}* скоро ответит вам!\n\n"
                f"Ожидайте ответа в этом чате."
            )
            
            # Notify operator
            from ..tasks import notify_operator_assignment
            notify_operator_assignment.delay(assignment.id, dialog.id)
        else:
            # No operators available
            self.api.send_text_message(
                phone,
                f"😔 К сожалению, все операторы сейчас заняты.\n\n"
                f"Позвоните нам: {settings.COMPANY_PHONE}\n"
                f"Или напишите, и мы ответим как можно скорее!"
            )
    
    def _send_help_message(self, phone: str):
        """Send help message with options."""
        text = "🤔 Не понял ваш запрос.\n\nВыберите действие:"
        self._send_help_buttons(phone, text)
    
    def _send_help_buttons(self, phone: str, text: str = "Выберите действие:"):
        """Send help buttons."""
        buttons = [
            {'id': 'btn_menu', 'title': '🏠 Главное меню'},
            {'id': 'btn_catalog', 'title': '📋 Каталог'},
            {'id': 'btn_operator', 'title': '👨‍💼 Оператор'}
        ]
        
        self.api.send_interactive_buttons(
            to=phone,
            body_text=text,
            buttons=buttons
        )
    
    def _save_bot_message(self, phone: str, text: str, response: dict):
        """Save bot response to database."""
        try:
            dialog = Dialog.objects.get(customer_phone=phone)
            Message.objects.create(
                dialog=dialog,
                whatsapp_message_id=response.get('messages', [{}])[0].get('id', ''),
                direction='bot',
                message_type='text',
                content=text
            )
        except Exception as e:
            logger.warning(f"Failed to save bot message: {e}")
    
    def _notify_operator(self, dialog: Dialog, message: dict, operator):
        """Notify operator about new message."""
        from ..tasks import notify_operator_new_message
        notify_operator_new_message.delay(
            dialog_id=dialog.id,
            operator_id=operator.id,
            message_content=self._extract_content(message)
        )
