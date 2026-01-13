# ==============================================
# CUSTOM EXCEPTION HANDLERS
# ==============================================
"""
Custom exception handling for REST API responses.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent API error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response format
        custom_response_data = {
            'success': False,
            'error': {
                'message': get_error_message(response.data),
                'code': response.status_code,
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        response.data = custom_response_data
    else:
        # Handle unexpected exceptions
        logger.exception(f"Unhandled exception: {exc}")
        response = Response({
            'success': False,
            'error': {
                'message': 'Произошла внутренняя ошибка сервера',
                'code': 500,
                'details': {}
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response


def get_error_message(data):
    """
    Extract a human-readable error message from response data.
    """
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        if 'non_field_errors' in data:
            return str(data['non_field_errors'][0])
        # Get first field error
        for field, errors in data.items():
            if isinstance(errors, list) and errors:
                return f"{field}: {errors[0]}"
            return f"{field}: {errors}"
    elif isinstance(data, list) and data:
        return str(data[0])
    return str(data)


class BusinessLogicError(Exception):
    """
    Custom exception for business logic errors.
    """
    def __init__(self, message, code='business_error'):
        self.message = message
        self.code = code
        super().__init__(message)


class WhatsAppAPIError(Exception):
    """
    Exception for WhatsApp API errors.
    """
    def __init__(self, message, error_code=None, response_data=None):
        self.message = message
        self.error_code = error_code
        self.response_data = response_data
        super().__init__(message)


class SpeechRecognitionError(Exception):
    """
    Exception for speech-to-text errors.
    """
    def __init__(self, message, original_error=None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)
