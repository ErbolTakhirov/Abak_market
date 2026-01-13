# ==============================================
# PAYMENTS SERIALIZERS
# ==============================================

from rest_framework import serializers
from .models import PaymentMethod, PaymentRequisite


class PaymentRequisiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRequisite
        fields = ['id', 'name', 'value', 'holder_name', 'is_primary']


class PaymentMethodSerializer(serializers.ModelSerializer):
    requisites = PaymentRequisiteSerializer(many=True, read_only=True)
    whatsapp_text = serializers.CharField(read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'method_type', 'details',
            'instructions', 'qr_image', 'requisites', 'whatsapp_text'
        ]
