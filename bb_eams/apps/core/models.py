from django.db import models
import uuid
from django.utils import timezone

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Device(BaseModel):
    name = models.CharField(max_length=100)
    device_serial = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=50, default='fingerprint')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.IntegerField(default=4370)
    location = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='offline')
    last_communication = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'devices'

class AuditLog(BaseModel):
    user_id = models.UUIDField()
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'audit_logs'

class Notification(BaseModel):
    NOTIFICATION_TYPES = (
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )
    
    user_id = models.UUIDField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    title = models.CharField(max_length=100)
    message = models.TextField()
    status = models.CharField(max_length=20, default='pending') # pending, sent, read
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'

class Policy(BaseModel):
    POLICY_TYPES = (
        ('attendance', 'Attendance'),
        ('leave', 'Leave'),
        ('overtime', 'Overtime'),
    )
    
    name = models.CharField(max_length=100)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    description = models.TextField(blank=True)
    rules = models.JSONField(default=dict)
    department_id = models.UUIDField(null=True, blank=True)
    effective_from = models.DateField()
    
    class Meta:
        db_table = 'policies'