# ==============================================
# WHATSAPP WEBHOOK VIEW
# ==============================================
"""
Main webhook handler for WhatsApp Business API.
Handles incoming messages and verification.
"""

import json
import hmac
import hashlib
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .handlers.message_handler import MessageHandler

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """
    WhatsApp Cloud API Webhook Handler.
    
    GET: Webhook verification
    POST: Receive incoming messages
    """
    
    def get(self, request):
        """
        Handle webhook verification from Meta.
        """
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        logger.info(f"Webhook verification: mode={mode}, token={token[:10]}...")
        
        if mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return HttpResponse(challenge, content_type='text/plain')
        
        logger.warning("Webhook verification failed")
        return HttpResponse('Verification failed', status=403)
    
    def post(self, request):
        """
        Handle incoming webhook events.
        """
        # Verify signature
        if not self._verify_signature(request):
            logger.warning("Invalid webhook signature")
            return HttpResponse('Invalid signature', status=401)
        
        try:
            payload = json.loads(request.body.decode('utf-8'))
            logger.debug(f"Webhook payload: {json.dumps(payload, indent=2)}")
            
            # Process the webhook
            self._process_webhook(payload)
            
            # Always return 200 quickly to acknowledge receipt
            return HttpResponse('OK', status=200)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return HttpResponse('Invalid JSON', status=400)
        except Exception as e:
            logger.exception(f"Webhook processing error: {e}")
            # Still return 200 to prevent retries
            return HttpResponse('OK', status=200)
    
    def _verify_signature(self, request) -> bool:
        """
        Verify the webhook signature from Meta.
        """
        signature = request.headers.get('X-Hub-Signature-256', '')
        
        if not signature or not settings.WHATSAPP_APP_SECRET:
            # Skip verification if not configured (development)
            if settings.DEBUG:
                return True
            return False
        
        try:
            # Extract signature hash
            signature_hash = signature.replace('sha256=', '')
            
            # Calculate expected hash
            expected_hash = hmac.new(
                settings.WHATSAPP_APP_SECRET.encode('utf-8'),
                request.body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature_hash, expected_hash)
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    def _process_webhook(self, payload: dict):
        """
        Process webhook payload and dispatch to handlers.
        """
        entry = payload.get('entry', [])
        
        for item in entry:
            changes = item.get('changes', [])
            
            for change in changes:
                value = change.get('value', {})
                
                # Handle messages
                messages = value.get('messages', [])
                for message in messages:
                    self._handle_message(message, value)
                
                # Handle status updates
                statuses = value.get('statuses', [])
                for status in statuses:
                    self._handle_status(status)
    
    def _handle_message(self, message: dict, value: dict):
        """
        Handle incoming message.
        """
        try:
            # Get contact info
            contacts = value.get('contacts', [])
            contact = contacts[0] if contacts else {}
            
            # Create message handler
            handler = MessageHandler()
            
            # Process message asynchronously
            from .tasks import process_incoming_message
            process_incoming_message.delay(
                message=message,
                contact=contact,
                metadata=value.get('metadata', {})
            )
            
        except Exception as e:
            logger.exception(f"Error handling message: {e}")
    
    def _handle_status(self, status: dict):
        """
        Handle message status update.
        """
        message_id = status.get('id')
        status_type = status.get('status')
        
        logger.info(f"Message {message_id} status: {status_type}")
        
        # Update message status in database
        from apps.dialogs.models import Message
        
        try:
            msg = Message.objects.filter(whatsapp_message_id=message_id).first()
            if msg:
                msg.delivery_status = status_type
                msg.save(update_fields=['delivery_status'])
        except Exception as e:
            logger.error(f"Error updating message status: {e}")
