from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.core.models import BaseModel
import uuid
from django.utils import timezone
import bcrypt

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        
        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    USER_TYPES = (
        ('employee', 'Employee'),
        ('hr_officer', 'HR Officer'),
        ('admin', 'Administrator'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    )
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='employee')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Employee specific fields
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    department_id = models.UUIDField(null=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    
    # Profile
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    address = models.TextField(blank=True)
    
    # Biometric status
    biometric_enrolled = models.BooleanField(default=False)
    last_biometric_sync = models.DateTimeField(null=True, blank=True)
    
    # Security
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    
    # Preferences
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['employee_id']),
            models.Index(fields=['user_type']),
            models.Index(fields=['status']),
        ]

class Department(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return self.name

class Role(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list)  # List of permission codes

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'roles'

class UserRole(BaseModel):
    user_id = models.UUIDField()
    role_id = models.UUIDField()
    assigned_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'user_roles'
        unique_together = ('user_id', 'role_id')

class EmployeeDetail(BaseModel):
    user_id = models.UUIDField(unique=True)
    department_id = models.UUIDField(null=True, blank=True)
    manager_id = models.UUIDField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    
    # Employment details
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)
    
    # Bank details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)
    
    # Documents
    documents = models.JSONField(default=list, blank=True)  # List of document URLs

    class Meta:
        db_table = 'employee_details'

class BiometricTemplate(BaseModel):
    BIOMETRIC_TYPES = (
        ('fingerprint', 'Fingerprint'),
        ('face', 'Facial Recognition'),
    )
    
    user_id = models.UUIDField()
    biometric_type = models.CharField(max_length=20, choices=BIOMETRIC_TYPES)
    template_data = models.BinaryField()  # Encrypted template
    template_hash = models.CharField(max_length=256)  # For verification
    quality_score = models.FloatField(default=0.0)
    enrolled_by = models.UUIDField(null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'biometric_templates'
        indexes = [
            models.Index(fields=['user_id', 'biometric_type']),
        ]