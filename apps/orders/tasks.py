# ==============================================
# ORDERS CELERY TASKS
# ==============================================
"""
Background tasks for order processing and notifications.
"""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.orders.tasks.notify_new_order')
def notify_new_order(order_id: int):
    """
    Send notifications about new order to operators.
    """
    from .models import Order
    from apps.users.models import User
    from apps.whatsapp_bot.services.whatsapp_api import WhatsAppAPI
    
    try:
        order = Order.objects.get(id=order_id)
        
        # Get operators who should be notified
        operators = User.objects.filter(
            role__in=[User.Role.OPERATOR, User.Role.ADMIN],
            is_active=True,
            notify_on_new_order=True
        )
        
        # Prepare notification message
        message = f"""
🆕 *Новый заказ #{order.order_number}*

👤 Клиент: {order.customer_name}
📞 Телефон: {order.customer_phone}
📍 Адрес: {order.customer_address or 'Не указан'}

💰 Сумма: {order.total} ₽
📦 Позиций: {order.items_count}

Источник: {order.get_source_display()}
        """.strip()
        
        # Send notifications via WhatsApp to operators
        wa_api = WhatsAppAPI()
        
        for operator in operators:
            if operator.phone:
                try:
                    wa_api.send_text_message(
                        to=operator.phone.replace('+', ''),
                        text=message
                    )
                except Exception as e:
                    logger.error(f"Failed to notify operator {operator.id}: {e}")
        
        logger.info(f"Notified {operators.count()} operators about order {order.order_number}")
        return {'status': 'success', 'notified': operators.count()}
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return {'status': 'error', 'message': 'Order not found'}
    except Exception as e:
        logger.error(f"Failed to notify about order {order_id}: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.orders.tasks.send_order_confirmation')
def send_order_confirmation(order_id: int):
    """
    Send order confirmation to customer via WhatsApp.
    """
    from .models import Order
    from apps.whatsapp_bot.services.whatsapp_api import WhatsAppAPI
    
    try:
        order = Order.objects.get(id=order_id)
        
        # Build items list
        items_text = ""
        for item in order.items.all():
            items_text += f"• {item.product_name} x{item.quantity} — {item.total} ₽\n"
        
        message = f"""
✅ *Заказ #{order.order_number} оформлен!*

{items_text}
💰 *Итого: {order.total} ₽*

Мы свяжемся с вами для подтверждения.

Спасибо за заказ! 🙏
        """.strip()
        
        # Send to customer
        wa_api = WhatsAppAPI()
        wa_api.send_text_message(
            to=order.customer_phone.replace('+', ''),
            text=message
        )
        
        logger.info(f"Sent confirmation for order {order.order_number}")
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f"Failed to send confirmation for order {order_id}: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.orders.tasks.cleanup_old_orders')
def cleanup_old_orders():
    """
    Archive or cleanup old completed/cancelled orders.
    Runs daily.
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import Order
    
    # Orders older than 90 days
    cutoff = timezone.now() - timedelta(days=90)
    
    old_orders = Order.objects.filter(
        status__in=[Order.Status.COMPLETED, Order.Status.CANCELLED],
        updated_at__lt=cutoff
    )
    
    count = old_orders.count()
    
    # In production, you might archive these instead of deleting
    # old_orders.delete()
    
    logger.info(f"Found {count} old orders for cleanup")
    return {'status': 'success', 'count': count}
