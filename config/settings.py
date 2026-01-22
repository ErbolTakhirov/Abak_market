# ==============================================
# DJANGO SETTINGS - PRODUCTION READY
# ==============================================
"""
Grocery Store + WhatsApp Bot Settings
Production-ready configuration with security best practices.
"""

import os
from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

# ==============================================
# BASE CONFIGURATION
# ==============================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,abak-market.onrender.com', cast=Csv())

# Force add production domains to ensure they work regardless of environment variables
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS + ['abakmarket.store', 'www.abakmarket.store', 'abak-market.onrender.com']))


# ==============================================
# APPLICATION DEFINITION
# ==============================================

# ... (skipped content) ...

# ==============================================
# CORS CONFIGURATION
# ==============================================

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv()
)

# Force add production domains
CORS_ALLOWED_ORIGINS = list(set(CORS_ALLOWED_ORIGINS + [
    'https://abakmarket.store', 
    'https://www.abakmarket.store', 
    'https://abak-market.onrender.com'
]))

CORS_ALLOW_CREDENTIALS = True


# ==============================================
# CSRF CONFIGURATION
# ==============================================

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv()
)

# Force add production domains
CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS + [
    'https://abakmarket.store', 
    'https://www.abakmarket.store', 
    'https://abak-market.onrender.com'
]))


# ==============================================
# SECURITY SETTINGS (Production)
# ==============================================

# ==============================================
# SECURITY SETTINGS (Production)
# ==============================================

if not DEBUG:
    # SSL/HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    
    # Cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Other security headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Whitenoise Storage (Compression + Caching)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ==============================================
# CELERY CONFIGURATION
# ==============================================

CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

CELERY_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_TIME_LIMIT = 600

CELERY_TASK_ROUTES = {
    'apps.whatsapp_bot.tasks.process_voice_message': {'queue': 'voice'},
    'apps.whatsapp_bot.tasks.send_pdf_catalog': {'queue': 'pdf'},
    'apps.whatsapp_bot.tasks.send_notification': {'queue': 'notifications'},
}

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-dialogs': {
        'task': 'apps.dialogs.tasks.cleanup_old_dialogs',
        'schedule': timedelta(hours=24),
    },
    'sync-catalog-cache': {
        'task': 'apps.catalog.tasks.sync_catalog_cache',
        'schedule': timedelta(minutes=15),
    },
}


# ==============================================
# WHATSAPP CONFIGURATION
# ==============================================

WHATSAPP_API_TOKEN = config('WHATSAPP_API_TOKEN', default='')
WHATSAPP_PHONE_NUMBER_ID = config('WHATSAPP_PHONE_NUMBER_ID', default='')
WHATSAPP_BUSINESS_ACCOUNT_ID = config('WHATSAPP_BUSINESS_ACCOUNT_ID', default='')
WHATSAPP_VERIFY_TOKEN = config('WHATSAPP_VERIFY_TOKEN', default='grocery-webhook-verify')
WHATSAPP_APP_SECRET = config('WHATSAPP_APP_SECRET', default='')
WHATSAPP_API_VERSION = 'v18.0'
WHATSAPP_API_URL = f'https://graph.facebook.com/{WHATSAPP_API_VERSION}'


# ==============================================
# SPEECH-TO-TEXT CONFIGURATION
# ==============================================

GOOGLE_APPLICATION_CREDENTIALS = config('GOOGLE_APPLICATION_CREDENTIALS', default='')
GOOGLE_CLOUD_PROJECT_ID = config('GOOGLE_CLOUD_PROJECT_ID', default='')

# OpenAI Whisper as alternative
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# Speech-to-Text Backend: 'google', 'openai', or 'local'
STT_BACKEND = config('STT_BACKEND', default='local')
# Local Whisper model: 'tiny', 'base', 'small', 'medium', 'large'
WHISPER_MODEL = config('WHISPER_MODEL', default='base')


# ==============================================
# COMPANY CONFIGURATION
# ==============================================

COMPANY_NAME = config('COMPANY_NAME', default='Абак маркет')
COMPANY_PHONE = config('COMPANY_PHONE', default='+7 (000) 000-00-00')
COMPANY_ADDRESS = config('COMPANY_ADDRESS', default='Адрес скоро появится')
COMPANY_WHATSAPP = config('COMPANY_WHATSAPP', default='')
COMPANY_DESCRIPTION = 'Свежие продукты и готовые блюда'


# ==============================================
# LOGGING CONFIGURATION
# ==============================================

LOG_LEVEL = config('LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'apps.whatsapp_bot': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Add file logging only if DEBUG is True (Local Development)
if DEBUG:
    # Ensure logs directory exists
    LOGS_DIR = BASE_DIR / 'logs'
    LOGS_DIR.mkdir(exist_ok=True)
    
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': LOGS_DIR / 'django.log',
        'maxBytes': 1024 * 1024 * 10,
        'backupCount': 5,
        'formatter': 'verbose',
    }
    LOGGING['loggers']['django']['handlers'].append('file')


# ==============================================
# SENTRY ERROR TRACKING (Production)
# ==============================================

SENTRY_DSN = config('SENTRY_DSN', default='')

if SENTRY_DSN and SENTRY_DSN.startswith('http') and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment='production',
        )
    except Exception:
        pass

# ==============================================
# DEBUG TOOLBAR CONFIGURATION
# ==============================================

if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
        INTERNAL_IPS = ['127.0.0.1', '::1', 'localhost']
        
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        }
    except ImportError:
        pass


# ==============================================
# JAZZMIN ADMIN THEME CONFIGURATION
# ==============================================

JAZZMIN_SETTINGS = {
    # Title on the login page
    "site_title": "Абак маркет",
    
    # Title on the brand (main navigation)
    "site_header": "Абак маркет",
    
    # Title in the browser tab
    "site_brand": "Абак",
    
    # Welcome text on the login page
    "welcome_sign": "Добро пожаловать в панель управления",
    
    # Copyright text
    "copyright": "Абак маркет © 2024",
    
    # Search models
    "search_model": ["catalog.Product", "orders.Order", "users.User"],
    
    # User menu links
    "usermenu_links": [
        {"name": "Сайт", "url": "/", "new_window": True, "icon": "fas fa-globe"},
        {"model": "users.user"},
    ],
    
    # Top menu
    "topmenu_links": [
        {"name": "Главная", "url": "admin:index", "icon": "fas fa-home"},
        {"name": "Сайт", "url": "/", "new_window": True, "icon": "fas fa-globe"},
        {"name": "Меню", "url": "/catalog/menu/", "new_window": True, "icon": "fas fa-utensils"},
    ],
    
    # Show sidebar
    "show_sidebar": True,
    "navigation_expanded": True,
    
    # Hide apps from sidebar
    "hide_apps": [],
    
    # Hide models from sidebar
    "hide_models": [],
    
    # Order of apps in sidebar
    "order_with_respect_to": [
        "catalog",
        "orders", 
        "users",
        "payments",
        "dialogs",
        "auth",
    ],
    
    # Icons for apps
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "users.User": "fas fa-user-tie",
        "users.OperatorAssignment": "fas fa-headset",
        "catalog.Category": "fas fa-tags",
        "catalog.Product": "fas fa-box",
        "catalog.ProductImage": "fas fa-images",
        "catalog.PDFCatalog": "fas fa-file-pdf",
        "orders.Order": "fas fa-shopping-cart",
        "orders.OrderItem": "fas fa-list",
        "payments.PaymentCredentials": "fas fa-credit-card",
        "dialogs.Dialog": "fas fa-comments",
        "dialogs.Message": "fas fa-comment",
    },
    
    # Default icon
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-file",
    
    # Customization
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    
    # Change view settings
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "users.user": "collapsible",
        "catalog.product": "horizontal_tabs",
        "orders.order": "vertical_tabs",
    },
}

# Jazzmin UI Tweaks
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-teal",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
