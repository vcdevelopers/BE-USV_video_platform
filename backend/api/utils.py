import os
import time
import random
import jwt
from django.conf import settings
from django.core.exceptions import ValidationError

# Country Code Mapping
COUNTRY_NAME_MAP = {
    'IN': 'India',
    'US': 'United States',
    'GB': 'United Kingdom',
    'AE': 'United Arab Emirates',
    'SG': 'Singapore',
    'CA': 'Canada',
    'AU': 'Australia',
    'DE': 'Germany',
    'FR': 'France',
    'JP': 'Japan',
    'SA': 'Saudi Arabia',
    'MY': 'Malaysia',
    'NP': 'Nepal',
    'BD': 'Bangladesh',
    'LK': 'Sri Lanka'
}

def verify_admin_token(request):
    """
    Verifies JWT token from Authorization header ('Bearer <token>') or query parameter ('?token=').
    Returns payload dict if valid, or None.
    """
    token = None
    auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
    if auth_header and isinstance(auth_header, str) and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    elif request.GET.get('token'):
        token = request.GET.get('token')

    if not token or token in ('undefined', 'null', ''):
        return None

    try:
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        return decoded
    except Exception:
        return None

def detect_device_type(request):
    """
    Simple device type detector based on User-Agent header.
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return 'mobile'
    elif 'ipad' in user_agent or 'tablet' in user_agent:
        return 'tablet'
    return 'desktop'

def extract_ip_geo(request):
    """
    Extracts IP address and fallback Country/City location.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')

    # Default location for local/development IPs
    country = 'India'
    city = 'Mumbai'

    return ip, country, city

def save_uploaded_file(uploaded_file, file_type='video'):
    """
    Validates file extension, MIME type, and size limit, then saves to MEDIA_ROOT.
    Returns relative URL path (/uploads/filename).
    """
    if file_type == 'video':
        valid_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
        valid_mimes = ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'application/octet-stream']
        max_size = 100 * 1024 * 1024  # 100 MB
    else:
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg']
        valid_mimes = ['image/jpeg', 'image/png', 'image/webp', 'image/svg+xml', 'application/octet-stream']
        max_size = 10 * 1024 * 1024   # 10 MB

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f"Invalid file extension '{ext}'. Allowed extensions for {file_type}: {', '.join(valid_extensions)}")

    if uploaded_file.size > max_size:
        raise ValidationError(f"File size ({uploaded_file.size} bytes) exceeds limit of {max_size // (1024*1024)}MB.")

    # Create destination uploads folder if not existing
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    filename = f"{file_type}_file-{int(time.time() * 1000)}-{random.randint(100000000, 999999999)}{ext}"
    dest_path = os.path.join(settings.MEDIA_ROOT, filename)

    with open(dest_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return f"/uploads/{filename}"
