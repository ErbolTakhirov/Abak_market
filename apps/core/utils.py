# ==============================================
# CORE UTILITIES
# ==============================================
"""
Utility functions used across the application.
"""

import os
import uuid
import hashlib
import re
from datetime import datetime
from typing import Optional
from django.utils.text import slugify as django_slugify
from django.core.cache import cache
import phonenumbers


def generate_uuid():
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate a short unique ID for orders, etc."""
    return uuid.uuid4().hex[:length].upper()


def slugify_ru(text: str) -> str:
    """
    Create URL-safe slug from Russian text.
    Transliterates Cyrillic characters.
    """
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    
    text = text.lower()
    result = []
    for char in text:
        if char in translit_map:
            result.append(translit_map[char])
        else:
            result.append(char)
    
    return django_slugify(''.join(result))


def format_phone_number(phone: str, country_code: str = 'RU') -> Optional[str]:
    """
    Format and validate phone number.
    Returns E.164 format or None if invalid.
    """
    try:
        parsed = phonenumbers.parse(phone, country_code)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, 
                phonenumbers.PhoneNumberFormat.E164
            )
    except phonenumbers.NumberParseException:
        pass
    return None


def normalize_phone_for_whatsapp(phone: str) -> str:
    """
    Normalize phone number for WhatsApp API.
    Removes '+' and any non-digit characters.
    """
    # Remove all non-digits
    clean = re.sub(r'\D', '', phone)
    
    # Handle Russian numbers
    if clean.startswith('8') and len(clean) == 11:
        clean = '7' + clean[1:]
    
    return clean


def format_price(amount: float, currency: str = 'RUB') -> str:
    """Format price with currency symbol."""
    currency_symbols = {
        'RUB': '₽',
        'USD': '$',
        'EUR': '€',
        'KZT': '₸',
    }
    symbol = currency_symbols.get(currency, currency)
    
    # Format with thousand separators
    formatted = f"{amount:,.0f}".replace(',', ' ')
    return f"{formatted} {symbol}"


def get_upload_path(instance, filename: str, folder: str = 'uploads') -> str:
    """
    Generate unique upload path for files.
    Organizes files by date and model.
    """
    ext = filename.split('.')[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    
    date_path = datetime.now().strftime('%Y/%m/%d')
    model_name = instance.__class__.__name__.lower()
    
    return os.path.join(folder, model_name, date_path, unique_name)


def get_product_image_path(instance, filename: str) -> str:
    """Upload path for product images."""
    return get_upload_path(instance, filename, 'products')


def get_category_image_path(instance, filename: str) -> str:
    """Upload path for category images."""
    return get_upload_path(instance, filename, 'categories')


def get_audio_upload_path(instance, filename: str) -> str:
    """Upload path for voice messages."""
    return get_upload_path(instance, filename, 'voice_messages')


def cache_response(key: str, timeout: int = 300):
    """
    Decorator to cache function results.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{key}:{hash(str(args) + str(kwargs))}"
            result = cache.get(cache_key)
            
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate all cache keys matching pattern.
    Note: Works with Redis backend.
    """
    from django_redis import get_redis_connection
    
    try:
        redis = get_redis_connection("default")
        keys = redis.keys(f"*{pattern}*")
        if keys:
            redis.delete(*keys)
    except Exception:
        # Fallback: clear entire cache
        cache.clear()


def calculate_hash(data: bytes) -> str:
    """Calculate SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to max length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path separators
    filename = os.path.basename(filename)
    
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext}"


def parse_menu_command(text: str) -> Optional[str]:
    """
    Parse user message to detect menu commands.
    Returns command name or None.
    """
    text = text.lower().strip()
    
    # Menu trigger words
    menu_triggers = ['меню', 'menu', 'начать', 'start', 'помощь', 'help']
    if any(trigger in text for trigger in menu_triggers):
        return 'menu'
    
    # Catalog triggers
    catalog_triggers = ['каталог', 'catalog', 'товары', 'products', 'продукты']
    if any(trigger in text for trigger in catalog_triggers):
        return 'catalog'
    
    # Payment triggers
    payment_triggers = ['оплата', 'payment', 'реквизиты', 'оплатить']
    if any(trigger in text for trigger in payment_triggers):
        return 'payment'
    
    # Operator triggers
    operator_triggers = ['оператор', 'operator', 'менеджер', 'человек', 'живой']
    if any(trigger in text for trigger in operator_triggers):
        return 'operator'
    
    return None
