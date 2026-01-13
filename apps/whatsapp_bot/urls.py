# ==============================================
# WHATSAPP BOT URLS
# ==============================================

from django.urls import path
from .views import WhatsAppWebhookView

app_name = 'whatsapp_bot'

urlpatterns = [
    path('webhook/', WhatsAppWebhookView.as_view(), name='webhook'),
]
