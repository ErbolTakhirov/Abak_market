# ==============================================
# DIALOGS CELERY TASKS
# ==============================================

from celery import shared_task
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name='apps.dialogs.tasks.cleanup_old_dialogs')
def cleanup_old_dialogs():
    """
    Cleanup old inactive dialogs.
    Runs daily.
    """
    from django.utils import timezone
    from .models import Dialog
    
    # Dialogs with no messages for 90 days
    cutoff = timezone.now() - timedelta(days=90)
    
    old_dialogs = Dialog.objects.filter(
        is_active=True,
        last_message_at__lt=cutoff
    )
    
    # Mark as inactive
    count = old_dialogs.update(is_active=False)
    
    logger.info(f"Marked {count} old dialogs as inactive")
    return {'status': 'success', 'count': count}


@shared_task(name='apps.dialogs.tasks.export_dialog_history')
def export_dialog_history(dialog_id: int, format: str = 'json'):
    """
    Export dialog history for backup or reporting.
    """
    from .models import Dialog, Message
    import json
    from django.core.files.storage import default_storage
    
    try:
        dialog = Dialog.objects.get(id=dialog_id)
        messages = Message.objects.filter(dialog=dialog).order_by('created_at')
        
        export_data = {
            'dialog': {
                'id': dialog.id,
                'customer_phone': dialog.customer_phone,
                'customer_name': dialog.customer_name,
                'created_at': str(dialog.created_at),
            },
            'messages': [
                {
                    'direction': msg.direction,
                    'type': msg.message_type,
                    'content': msg.content,
                    'created_at': str(msg.created_at)
                }
                for msg in messages
            ]
        }
        
        # Save to file
        filename = f"exports/dialog_{dialog_id}_{dialog.customer_phone}.json"
        content = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        default_storage.save(filename, content.encode('utf-8'))
        
        logger.info(f"Exported dialog {dialog_id}")
        return {'status': 'success', 'filename': filename}
        
    except Dialog.DoesNotExist:
        logger.error(f"Dialog {dialog_id} not found")
        return {'status': 'error', 'message': 'Dialog not found'}
