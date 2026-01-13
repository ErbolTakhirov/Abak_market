# ==============================================
# PAYMENTS API URLS
# ==============================================

from django.urls import path
from .views import PaymentMethodListView

app_name = 'payments_api'

urlpatterns = [
    path('methods/', PaymentMethodListView.as_view(), name='methods'),
]
