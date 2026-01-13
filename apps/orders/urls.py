# ==============================================
# ORDERS API URLS
# ==============================================

from django.urls import path
from .views import OrderCreateView, OrderStatusView

app_name = 'orders_api'

urlpatterns = [
    path('create/', OrderCreateView.as_view(), name='create'),
    path('status/<str:order_number>/', OrderStatusView.as_view(), name='status'),
]
