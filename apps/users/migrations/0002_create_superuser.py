# ==============================================
# AUTO-CREATE SUPERUSER MIGRATION
# ==============================================
"""
Automatically creates a superuser if environment variables are set.
This runs during deployment.
"""

import os
from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_superuser(apps, schema_editor):
    """Create superuser from environment variables."""
    User = apps.get_model('users', 'User')
    
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@abakmarket.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    
    # Skip if no password is set
    if not password:
        print("⚠️  DJANGO_SUPERUSER_PASSWORD not set, skipping superuser creation")
        return
    
    # Skip if user already exists
    if User.objects.filter(email=email).exists():
        print(f"✅ Superuser '{email}' already exists")
        return
    
    # Create superuser
    User.objects.create(
        email=email,
        password=make_password(password),
        is_staff=True,
        is_superuser=True,
        is_active=True,
        role='admin',
    )
    print(f"✅ Superuser '{email}' created successfully!")


def reverse_superuser(apps, schema_editor):
    """Reverse migration - do nothing."""
    pass


class Migration(migrations.Migration):
    
    dependencies = [
        ('users', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(create_superuser, reverse_superuser),
    ]
