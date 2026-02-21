from django.db import models
from apps.core.models import BaseModel

class LeaveRequest(BaseModel):
    LEAVE_TYPES = (
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('bereavement', 'Bereavement Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('study', 'Study Leave'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    user_id = models.UUIDField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval workflow
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Applied policy
    applied_policy_id = models.UUIDField(null=True, blank=True)
    
    # Documents
    supporting_documents = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'leave_requests'
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

class LeaveBalance(BaseModel):
    user_id = models.UUIDField(unique=True)
    year = models.IntegerField()
    
    # Leave balances
    annual_total = models.IntegerField(default=20)
    annual_used = models.IntegerField(default=0)
    annual_remaining = models.IntegerField(default=20)
    
    sick_total = models.IntegerField(default=12)
    sick_used = models.IntegerField(default=0)
    sick_remaining = models.IntegerField(default=12)
    
    # Carry forward
    carried_forward = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leave_balances'
        unique_together = ('user_id', 'year')