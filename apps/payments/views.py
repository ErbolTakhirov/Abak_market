# ==============================================
# PAYMENTS API VIEWS
# ==============================================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import PaymentMethod
from .serializers import PaymentMethodSerializer


class PaymentMethodListView(APIView):
    """
    List active payment methods.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        methods = PaymentMethod.objects.filter(is_active=True).order_by('order')
        serializer = PaymentMethodSerializer(methods, many=True)
        
        return Response({
            'success': True,
            'methods': serializer.data
        })
