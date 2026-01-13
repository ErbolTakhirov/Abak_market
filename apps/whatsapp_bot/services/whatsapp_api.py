# ==============================================
# WHATSAPP API CLIENT
# ==============================================
"""
WhatsApp Cloud API client for sending messages.
Supports text, images, documents, and interactive messages.
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from django.conf import settings
from apps.core.exceptions import WhatsAppAPIError

logger = logging.getLogger(__name__)


class WhatsAppAPI:
    """
    WhatsApp Cloud API client.
    """
    
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_API_TOKEN
        
        self.base_url = f"{self.api_url}/{self.phone_number_id}/messages"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _send_request(self, payload: dict) -> dict:
        """
        Send request to WhatsApp API.
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers
                )
                
                response_data = response.json()
                
                if response.status_code != 200:
                    error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"WhatsApp API error: {error_msg}")
                    raise WhatsAppAPIError(
                        message=error_msg,
                        error_code=response.status_code,
                        response_data=response_data
                    )
                
                logger.debug(f"WhatsApp API response: {response_data}")
                return response_data
                
        except httpx.RequestError as e:
            logger.error(f"WhatsApp API request failed: {e}")
            raise WhatsAppAPIError(f"Request failed: {e}")
    
    def send_text_message(self, to: str, text: str, preview_url: bool = False) -> dict:
        """
        Send a text message.
        
        Args:
            to: Recipient phone number (without +)
            text: Message text (supports formatting)
            preview_url: Whether to show URL previews
        
        Returns:
            API response with message ID
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'text',
            'text': {
                'preview_url': preview_url,
                'body': text
            }
        }
        
        return self._send_request(payload)
    
    def send_image(self, to: str, image_url: str, caption: str = '') -> dict:
        """
        Send an image message.
        
        Args:
            to: Recipient phone number
            image_url: URL of the image
            caption: Optional caption
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'image',
            'image': {
                'link': image_url,
                'caption': caption
            }
        }
        
        return self._send_request(payload)
    
    def send_document(self, to: str, document_url: str, filename: str, caption: str = '') -> dict:
        """
        Send a document (PDF, etc.).
        
        Args:
            to: Recipient phone number
            document_url: URL of the document
            filename: Display filename
            caption: Optional caption
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'document',
            'document': {
                'link': document_url,
                'filename': filename,
                'caption': caption
            }
        }
        
        return self._send_request(payload)
    
    def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: str = '',
        footer_text: str = ''
    ) -> dict:
        """
        Send interactive message with buttons.
        
        Args:
            to: Recipient phone number
            body_text: Main message text
            buttons: List of buttons [{'id': 'btn_1', 'title': 'Button 1'}, ...]
            header_text: Optional header
            footer_text: Optional footer
        """
        # Build buttons structure (max 3 buttons)
        button_list = []
        for btn in buttons[:3]:
            button_list.append({
                'type': 'reply',
                'reply': {
                    'id': btn['id'],
                    'title': btn['title'][:20]  # Max 20 chars
                }
            })
        
        interactive = {
            'type': 'button',
            'body': {'text': body_text},
            'action': {'buttons': button_list}
        }
        
        if header_text:
            interactive['header'] = {'type': 'text', 'text': header_text}
        
        if footer_text:
            interactive['footer'] = {'text': footer_text}
        
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'interactive',
            'interactive': interactive
        }
        
        return self._send_request(payload)
    
    def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict],
        header_text: str = '',
        footer_text: str = ''
    ) -> dict:
        """
        Send interactive message with list selection.
        
        Args:
            to: Recipient phone number
            body_text: Main message text
            button_text: Button text to show list
            sections: List sections with rows
            header_text: Optional header
            footer_text: Optional footer
        """
        interactive = {
            'type': 'list',
            'body': {'text': body_text},
            'action': {
                'button': button_text[:20],
                'sections': sections
            }
        }
        
        if header_text:
            interactive['header'] = {'type': 'text', 'text': header_text}
        
        if footer_text:
            interactive['footer'] = {'text': footer_text}
        
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'interactive',
            'interactive': interactive
        }
        
        return self._send_request(payload)
    
    def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = 'ru',
        components: List[Dict] = None
    ) -> dict:
        """
        Send a template message.
        
        Args:
            to: Recipient phone number
            template_name: Approved template name
            language_code: Template language
            components: Template components (header, body params)
        """
        template = {
            'name': template_name,
            'language': {'code': language_code}
        }
        
        if components:
            template['components'] = components
        
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'template',
            'template': template
        }
        
        return self._send_request(payload)
    
    def mark_as_read(self, message_id: str) -> dict:
        """
        Mark a message as read.
        """
        payload = {
            'messaging_product': 'whatsapp',
            'status': 'read',
            'message_id': message_id
        }
        
        return self._send_request(payload)
    
    def download_media(self, media_id: str) -> bytes:
        """
        Download media file from WhatsApp.
        
        Args:
            media_id: WhatsApp media ID
        
        Returns:
            Media file bytes
        """
        try:
            # First, get the media URL
            media_url = f"{self.api_url}/{media_id}"
            
            with httpx.Client(timeout=60.0) as client:
                # Get media info
                response = client.get(media_url, headers=self.headers)
                media_data = response.json()
                
                download_url = media_data.get('url')
                if not download_url:
                    raise WhatsAppAPIError("Media URL not found")
                
                # Download the actual file
                media_response = client.get(
                    download_url,
                    headers={'Authorization': f'Bearer {self.access_token}'}
                )
                
                return media_response.content
                
        except Exception as e:
            logger.error(f"Failed to download media: {e}")
            raise WhatsAppAPIError(f"Media download failed: {e}")
