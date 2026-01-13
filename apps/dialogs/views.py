# ==============================================
# DIALOGS API VIEWS
# ==============================================
"""
API views for dialog management (operator interface).
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Dialog, Message
from .serializers import DialogSerializer, DialogDetailSerializer, MessageSerializer
from apps.whatsapp_bot.services.whatsapp_api import WhatsAppAPI


class DialogListView(APIView):
    """
    List all dialogs for operators.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        dialogs = Dialog.objects.filter(is_active=True).order_by('-last_message_at')
        
        # Filter by assigned
        if request.query_params.get('assigned') == 'true':
            dialogs = dialogs.filter(is_assigned=True)
        
        serializer = DialogSerializer(dialogs, many=True)
        
        return Response({
            'success': True,
            'dialogs': serializer.data
        })


class DialogDetailView(APIView):
    """
    Get dialog details with messages.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            dialog = Dialog.objects.get(pk=pk)
            serializer = DialogDetailSerializer(dialog)
            
            return Response({
                'success': True,
                'dialog': serializer.data
            })
        except Dialog.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Диалог не найден'
            }, status=status.HTTP_404_NOT_FOUND)


class SendMessageView(APIView):
    """
    Send message to customer from operator.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            dialog = Dialog.objects.get(pk=pk)
        except Dialog.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Диалог не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        text = request.data.get('text', '').strip()
        if not text:
            return Response({
                'success': False,
                'error': 'Сообщение не может быть пустым'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Send via WhatsApp API
            api = WhatsAppAPI()
            response = api.send_text_message(
                to=dialog.customer_phone,
                text=text
            )
            
            # Save message
            message = Message.objects.create(
                dialog=dialog,
                whatsapp_message_id=response.get('messages', [{}])[0].get('id', ''),
                direction='operator',
                message_type='text',
                content=text
            )
            
            return Response({
                'success': True,
                'message': MessageSerializer(message).data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
