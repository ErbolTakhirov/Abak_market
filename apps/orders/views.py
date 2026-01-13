# ==============================================
# ORDERS API VIEWS
# ==============================================
"""
API views for order creation and status checking.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction

from .models import Order, OrderItem
from .serializers import OrderCreateSerializer, OrderSerializer
from apps.catalog.models import Product


class OrderCreateView(APIView):
    """
    Create a new order.
    Used by both website and WhatsApp bot.
    """
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Create order
        order = Order.objects.create(
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            customer_address=data.get('customer_address', ''),
            customer_notes=data.get('customer_notes', ''),
            source=data.get('source', Order.Source.WHATSAPP),
            delivery_fee=data.get('delivery_fee', 0)
        )
        
        # Add items
        items_data = data.get('items', [])
        for item_data in items_data:
            product = Product.objects.filter(
                id=item_data['product_id'],
                is_available=True
            ).first()
            
            if product:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_price=product.price,
                    quantity=item_data.get('quantity', 1),
                    price=product.price,
                    notes=item_data.get('notes', '')
                )
        
        # Calculate totals
        order.calculate_totals()
        
        # Trigger notification tasks
        from .tasks import notify_new_order
        notify_new_order.delay(order.id)
        
        return Response({
            'success': True,
            'order': OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)


class OrderStatusView(APIView):
    """
    Check order status by order number.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number.upper())
            return Response({
                'success': True,
                'order': OrderSerializer(order).data
            })
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)
