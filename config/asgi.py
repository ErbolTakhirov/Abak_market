# ==============================================
# ASGI CONFIGURATION
# ==============================================
"""
ASGI config for Grocery Store project.
Used for async support if needed.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
