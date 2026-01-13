# ==============================================
# WHATSAPP BOT CELERY TASKS
# ==============================================
"""
Background tasks for WhatsApp bot operations.
"""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.whatsapp_bot.tasks.process_incoming_message', queue='default')
def process_incoming_message(message: dict, contact: dict, metadata: dict):
    """
    Process incoming WhatsApp message asynchronously.
    """
    from .handlers.message_handler import MessageHandler
    
    try:
        handler = MessageHandler()
        handler.handle(message, contact, metadata)
        
        logger.info(f"Processed message from {message.get('from')}")
        return {'status': 'success'}
        
    except Exception as e:
        logger.exception(f"Failed to process message: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.whatsapp_bot.tasks.process_voice_message', queue='voice')
def process_voice_message(dialog_id: int, message_id: int, audio_id: str, phone: str):
    """
    Process voice message: download, transcribe, analyze, respond.
    """
    from apps.dialogs.models import Dialog, Message
    from .services.whatsapp_api import WhatsAppAPI
    from .services.speech_to_text import SpeechToTextService
    
    api = WhatsAppAPI()
    
    try:
        # Download audio
        logger.info(f"Downloading audio {audio_id}")
        audio_data = api.download_media(audio_id)
        
        # Transcribe
        logger.info("Transcribing audio...")
        stt = SpeechToTextService()  # Uses settings.STT_BACKEND
        transcript = stt.transcribe(audio_data)
        
        if not transcript:
            api.send_text_message(
                phone,
                "🤔 Не удалось распознать сообщение. Попробуйте ещё раз или напишите текстом."
            )
            return {'status': 'empty_transcript'}
        
        # Update message with transcript
        try:
            msg = Message.objects.get(id=message_id)
            msg.content = f"[Голосовое]: {transcript}"
            msg.transcription = transcript
            msg.save()
        except Message.DoesNotExist:
            pass
        
        # Analyze intent
        intent = stt.analyze_intent(transcript)
        logger.info(f"Voice intent: {intent}")
        
        # Respond based on intent
        if intent['requires_operator']:
            # Complex query - connect to operator
            from apps.users.models import OperatorAssignment
            from apps.dialogs.models import Dialog
            
            dialog = Dialog.objects.get(id=dialog_id)
            
            api.send_text_message(
                phone,
                f"📝 Вы сказали: _{transcript}_\n\n"
                f"Переключаю на оператора для помощи..."
            )
            
            OperatorAssignment.assign_operator(phone)
            notify_operator_assignment.delay(None, dialog_id)
        else:
            # Simple command - handle automatically
            from .handlers.message_handler import MessageHandler
            
            api.send_text_message(
                phone,
                f"📝 Вы сказали: _{transcript}_"
            )
            
            # Process as text
            handler = MessageHandler()
            fake_message = {
                'from': phone,
                'type': 'text',
                'text': {'body': transcript},
                'id': f'voice_{message_id}'
            }
            
            dialog = Dialog.objects.get(id=dialog_id)
            handler._handle_text_message(dialog, fake_message)
        
        return {'status': 'success', 'transcript': transcript}
        
    except Exception as e:
        logger.exception(f"Voice processing failed: {e}")
        
        api.send_text_message(
            phone,
            "😔 Не удалось обработать голосовое сообщение. "
            "Пожалуйста, напишите текстом или позвоните нам."
        )
        
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.whatsapp_bot.tasks.send_pdf_catalog', queue='pdf')
def send_pdf_catalog(phone: str, category_id: int = None):
    """
    Send PDF catalog to customer.
    """
    from .services.whatsapp_api import WhatsAppAPI
    from apps.catalog.models import PDFCatalog
    
    api = WhatsAppAPI()
    
    try:
        # Get latest catalog
        if category_id:
            catalog = PDFCatalog.get_latest(category_id=category_id)
        else:
            catalog = PDFCatalog.get_latest()
        
        if not catalog or not catalog.file:
            # Generate new catalog
            from apps.catalog.tasks import generate_pdf_catalog
            result = generate_pdf_catalog(category_id)
            
            if result.get('status') == 'success':
                catalog = PDFCatalog.objects.get(id=result['catalog_id'])
            else:
                api.send_text_message(phone, "😔 Каталог временно недоступен.")
                return {'status': 'error', 'message': 'Catalog generation failed'}
        
        # Get full URL for catalog
        catalog_url = catalog.file.url
        if not catalog_url.startswith('http'):
            catalog_url = f"https://yourdomain.com{catalog_url}"
        
        # Send PDF
        api.send_document(
            to=phone,
            document_url=catalog_url,
            filename=f"{catalog.name}.pdf",
            caption=f"📄 {catalog.name}\n\nАктуально на: {catalog.updated_at.strftime('%d.%m.%Y')}"
        )
        
        logger.info(f"Sent PDF catalog to {phone}")
        return {'status': 'success'}
        
    except Exception as e:
        logger.exception(f"Failed to send PDF: {e}")
        
        api.send_text_message(
            phone,
            "😔 Не удалось отправить каталог. Попробуйте позже."
        )
        
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.whatsapp_bot.tasks.notify_operator_assignment', queue='notifications')
def notify_operator_assignment(assignment_id: int, dialog_id: int):
    """
    Notify operator about new assignment.
    """
    from apps.users.models import OperatorAssignment
    from apps.dialogs.models import Dialog
    from .services.whatsapp_api import WhatsAppAPI
    
    api = WhatsAppAPI()
    
    try:
        if assignment_id:
            assignment = OperatorAssignment.objects.get(id=assignment_id)
            operator = assignment.operator
        else:
            # Find any online operator
            from apps.users.models import User
            operator = User.objects.filter(
                role=User.Role.OPERATOR,
                is_active=True,
                is_online=True
            ).first()
        
        if not operator:
            logger.warning("No operator available for assignment")
            return {'status': 'no_operator'}
        
        dialog = Dialog.objects.get(id=dialog_id)
        
        # Get recent messages
        recent_messages = dialog.messages.order_by('-created_at')[:5]
        messages_text = ""
        for msg in reversed(recent_messages):
            prefix = "👤" if msg.direction == 'customer' else "🤖"
            messages_text += f"{prefix} {msg.content[:100]}\n"
        
        notification = f"""
🆕 *Новый клиент ожидает ответа*

👤 Клиент: {dialog.customer_name}
📞 Телефон: {dialog.customer_phone}

*Последние сообщения:*
{messages_text}

Ответьте клиенту через админ-панель или WhatsApp Business.
        """.strip()
        
        # Send to operator's phone if available
        if operator.phone:
            api.send_text_message(
                to=operator.phone.replace('+', ''),
                text=notification
            )
        
        logger.info(f"Notified operator {operator.id} about dialog {dialog_id}")
        return {'status': 'success'}
        
    except Exception as e:
        logger.exception(f"Failed to notify operator: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.whatsapp_bot.tasks.notify_operator_new_message', queue='notifications')
def notify_operator_new_message(dialog_id: int, operator_id: int, message_content: str):
    """
    Notify operator about new message in assigned dialog.
    """
    from apps.users.models import User
    from apps.dialogs.models import Dialog
    from .services.whatsapp_api import WhatsAppAPI
    
    try:
        dialog = Dialog.objects.get(id=dialog_id)
        operator = User.objects.get(id=operator_id)
        
        if operator.phone:
            api = WhatsAppAPI()
            
            notification = f"""
💬 *Новое сообщение от клиента*

👤 {dialog.customer_name}
📞 {dialog.customer_phone}

_{message_content[:200]}_
            """.strip()
            
            api.send_text_message(
                to=operator.phone.replace('+', ''),
                text=notification
            )
        
        return {'status': 'success'}
        
    except Exception as e:
        logger.exception(f"Failed to notify operator: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(name='apps.whatsapp_bot.tasks.send_broadcast', queue='notifications')
def send_broadcast(message: str, customer_phones: list = None, template_name: str = None):
    """
    Send broadcast message to multiple customers.
    Use templates for marketing messages (WhatsApp policy).
    """
    from .services.whatsapp_api import WhatsAppAPI
    from apps.dialogs.models import Dialog
    
    api = WhatsAppAPI()
    
    if not customer_phones:
        # Get all active dialogs
        dialogs = Dialog.objects.filter(is_active=True)
        customer_phones = [d.customer_phone for d in dialogs]
    
    success_count = 0
    
    for phone in customer_phones:
        try:
            if template_name:
                api.send_template(to=phone, template_name=template_name)
            else:
                api.send_text_message(to=phone, text=message)
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send to {phone}: {e}")
            continue
    
    logger.info(f"Broadcast sent to {success_count}/{len(customer_phones)} customers")
    return {'status': 'success', 'sent': success_count, 'total': len(customer_phones)}
