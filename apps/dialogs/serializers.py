# ==============================================
# DIALOGS SERIALIZERS
# ==============================================

from rest_framework import serializers
from .models import Dialog, Message


class MessageSerializer(serializers.ModelSerializer):
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'direction', 'direction_display', 'message_type',
            'content', 'transcription', 'media_url', 'delivery_status',
            'created_at'
        ]


class DialogSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Dialog
        fields = [
            'id', 'customer_phone', 'customer_name', 'is_active',
            'is_assigned', 'messages_count', 'last_message_at',
            'last_message', 'tags'
        ]
    
    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {
                'content': msg.content[:100],
                'direction': msg.direction,
                'created_at': msg.created_at
            }
        return None


class DialogDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Dialog
        fields = [
            'id', 'customer_phone', 'customer_name', 'is_active',
            'is_assigned', 'messages_count', 'tags', 'notes',
            'created_at', 'last_message_at', 'messages'
        ]
