# ==============================================
# ORDERS SERIALIZERS
# ==============================================
"""
Serializers for order API.
"""

from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'quantity', 'price', 'total', 'notes']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'source', 'source_display', 'customer_name', 'customer_phone',
            'customer_address', 'subtotal', 'delivery_fee', 'discount',
            'total', 'items', 'items_count', 'customer_notes',
            'created_at', 'updated_at'
        ]


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items."""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    notes = serializers.CharField(max_length=200, required=False, allow_blank=True)


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders."""
    customer_name = serializers.CharField(max_length=200)
    customer_phone = serializers.CharField(max_length=20)
    customer_address = serializers.CharField(required=False, allow_blank=True)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    source = serializers.ChoiceField(
        choices=Order.Source.choices,
        default=Order.Source.WHATSAPP
    )
    delivery_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    items = OrderItemCreateSerializer(many=True, required=False)
