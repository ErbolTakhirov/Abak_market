# ==============================================
# USER MODELS
# ==============================================
"""
Custom user model and operator management.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError(_('Email обязателен'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with roles for admin and operators.
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Администратор')
        OPERATOR = 'operator', _('Оператор')
        MANAGER = 'manager', _('Менеджер')
    
    # Basic fields
    email = models.EmailField(
        _('Email'),
        unique=True,
        error_messages={
            'unique': _('Пользователь с таким email уже существует.'),
        }
    )
    
    first_name = models.CharField(_('Имя'), max_length=150, blank=True)
    last_name = models.CharField(_('Фамилия'), max_length=150, blank=True)
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    
    # Role and permissions
    role = models.CharField(
        _('Роль'),
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATOR
    )
    
    # Status
    is_staff = models.BooleanField(
        _('Доступ к админке'),
        default=False,
        help_text=_('Определяет, может ли пользователь войти в админ-панель.')
    )
    is_active = models.BooleanField(
        _('Активен'),
        default=True,
        help_text=_('Определяет, активен ли аккаунт пользователя.')
    )
    is_online = models.BooleanField(
        _('Онлайн'),
        default=False,
        help_text=_('Доступен ли оператор для приёма звонков.')
    )
    
    # Timestamps
    date_joined = models.DateTimeField(_('Дата регистрации'), default=timezone.now)
    last_activity = models.DateTimeField(_('Последняя активность'), null=True, blank=True)
    
    # Telegram/WhatsApp notification settings
    telegram_id = models.CharField(
        _('Telegram ID'),
        max_length=50,
        blank=True,
        help_text=_('ID для получения уведомлений в Telegram')
    )
    notify_on_new_order = models.BooleanField(
        _('Уведомлять о новых заказах'),
        default=True
    )
    notify_on_operator_request = models.BooleanField(
        _('Уведомлять о запросе оператора'),
        default=True
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.get_full_name() or self.email
    
    def get_full_name(self):
        """Return full name with space."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.email
    
    def get_short_name(self):
        """Return first name."""
        return self.first_name or self.email.split('@')[0]
    
    @property
    def is_admin(self):
        """Check if user is admin."""
        return self.role == self.Role.ADMIN or self.is_superuser
    
    @property
    def is_operator(self):
        """Check if user is operator."""
        return self.role == self.Role.OPERATOR
    
    def set_online(self, status: bool = True):
        """Set operator online status."""
        self.is_online = status
        self.last_activity = timezone.now()
        self.save(update_fields=['is_online', 'last_activity'])


class OperatorAssignment(models.Model):
    """
    Track which operator is assigned to which customer conversation.
    """
    
    operator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('Оператор')
    )
    customer_phone = models.CharField(
        _('Телефон клиента'),
        max_length=20,
        db_index=True
    )
    is_active = models.BooleanField(
        _('Активно'),
        default=True
    )
    assigned_at = models.DateTimeField(
        _('Назначен'),
        auto_now_add=True
    )
    closed_at = models.DateTimeField(
        _('Закрыт'),
        null=True,
        blank=True
    )
    notes = models.TextField(
        _('Заметки'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('Назначение оператора')
        verbose_name_plural = _('Назначения операторов')
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['customer_phone', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.operator} -> {self.customer_phone}"
    
    def close(self):
        """Close assignment."""
        self.is_active = False
        self.closed_at = timezone.now()
        self.save(update_fields=['is_active', 'closed_at'])
    
    @classmethod
    def get_active_operator(cls, customer_phone: str):
        """Get currently assigned operator for customer."""
        assignment = cls.objects.filter(
            customer_phone=customer_phone,
            is_active=True
        ).select_related('operator').first()
        
        return assignment.operator if assignment else None
    
    @classmethod
    def assign_operator(cls, customer_phone: str, operator: User = None):
        """
        Assign an operator to customer.
        If no operator specified, assign to available operator.
        """
        # Close existing assignment
        cls.objects.filter(
            customer_phone=customer_phone,
            is_active=True
        ).update(is_active=False, closed_at=timezone.now())
        
        # Find available operator if not specified
        if operator is None:
            operator = User.objects.filter(
                role=User.Role.OPERATOR,
                is_active=True,
                is_online=True
            ).order_by('last_activity').first()
        
        if operator:
            return cls.objects.create(
                operator=operator,
                customer_phone=customer_phone
            )
        
        return None
