# ==============================================
# DIALOGS API URLS
# ==============================================

from django.urls import path
from .views import DialogListView, DialogDetailView, SendMessageView

app_name = 'dialogs_api'

urlpatterns = [
    path('', DialogListView.as_view(), name='list'),
    path('<int:pk>/', DialogDetailView.as_view(), name='detail'),
    path('<int:pk>/send/', SendMessageView.as_view(), name='send'),
]
