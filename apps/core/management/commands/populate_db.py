from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.catalog.models import Category, Product
from apps.payments.models import PaymentMethod
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Superuser
        if not User.objects.filter(email='admin@example.com').exists():
            User.objects.create_superuser(
                email='admin@example.com',
                password='admin',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin@example.com / admin'))

        # Categories
        categories_data = [
            {'name': 'Овощи и фрукты', 'icon': '🥬'},
            {'name': 'Молочные продукты', 'icon': '🥛'},
            {'name': 'Мясо и птица', 'icon': '🥩'},
            {'name': 'Выпечка', 'icon': '🍞'},
            {'name': 'Напитки', 'icon': '🥤'},
        ]
        
        categories = []
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=f"cat-{random.randint(1000, 9999)}", # Simplified slug
                defaults={'name': cat_data['name'], 'icon': cat_data['icon']}
            )
            categories.append(cat)
            
        # Products
        products_data = [
            ('Бананы', 120, 'кг'),
            ('Молоко 3.2%', 85, 'шт'),
            ('Хлеб Бородинский', 45, 'шт'),
            ('Куриное филе', 350, 'кг'),
            ('Яблоки Гала', 90, 'кг'),
            ('Картофель', 40, 'кг'),
            ('Сыр Российский', 650, 'кг'),
            ('Кола 1.5л', 110, 'шт'),
        ]
        
        for prod_name, price, unit in products_data:
            Product.objects.get_or_create(
                name=prod_name,
                defaults={
                    'category': random.choice(categories),
                    'price': price,
                    'unit': unit,
                    'short_description': f'Свежий {prod_name}',
                    'is_available': True,
                    'is_featured': random.choice([True, False])
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated database'))
