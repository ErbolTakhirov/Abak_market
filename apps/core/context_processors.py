# ==============================================
# TEMPLATE CONTEXT PROCESSORS
# ==============================================
"""
Context processors to inject site-wide settings into templates.
"""

from django.conf import settings


def site_settings(request):
    """
    Inject company and site settings into all templates.
    """
    return {
        'COMPANY_NAME': settings.COMPANY_NAME,
        'COMPANY_PHONE': settings.COMPANY_PHONE,
        'COMPANY_ADDRESS': settings.COMPANY_ADDRESS,
        'COMPANY_WHATSAPP': settings.COMPANY_WHATSAPP,
        'COMPANY_DESCRIPTION': getattr(settings, 'COMPANY_DESCRIPTION', ''),
        'DEBUG': settings.DEBUG,
    }
