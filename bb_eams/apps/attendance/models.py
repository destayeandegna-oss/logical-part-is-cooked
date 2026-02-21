from django.db import models
from apps.core.models import BaseModel
from django.utils import timezone

class Shift(BaseModel):
    name = models.CharField(max_length=100)
    department_id = models.UUIDField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_minutes = models.IntegerField(default=15)
    overtime_allowed = models.BooleanField(default=False)
    break_duration_minutes = models.IntegerField(default=60)
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

    class Meta:
        db_table = 'shifts'
        unique_together = ('name', 'department_id')

class Assignment(BaseModel):
    user_id = models.UUIDField()
    shift_id = models.UUIDField()
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
    assigned_by = models.UUIDField()
    
    class Meta:
        db_table = 'assignments'
        indexes = [
            models.Index(fields=['user_id', 'from_date']),
        ]

class AttendanceRecord(BaseModel):
    ATTENDANCE_TYPES = (
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
    )
    
    STATUS_CHOICES = (
        ('on_time', 'On Time'),
        ('late', 'Late'),
        ('early_exit', 'Early Exit'),
        ('overtime', 'Overtime'),
        ('missed', 'Missed'),
    )
    
    user_id = models.UUIDField()
    device_id = models.UUIDField()
    timestamp = models.DateTimeField(default=timezone.now)
    attendance_type = models.CharField(max_length=20, choices=ATTENDANCE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='on_time')
    
    # Verification data
    biometric_verified = models.BooleanField(default=True)
    verification_score = models.FloatField(default=1.0)
    template_used = models.UUIDField(null=True, blank=True)
    
    # Location data
    location_data = models.JSONField(default=dict, blank=True)
    
    # Sync status
    synced = models.BooleanField(default=True)
    sync_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'attendance_records'
        indexes = [
            models.Index(fields=['user_id', '-timestamp']),
            models.Index(fields=['device_id', 'timestamp']),
            models.Index(fields=['status']),
        ]
        ordering = ['-timestamp']

class DailyAttendance(BaseModel):
    user_id = models.UUIDField(unique_for_date='date')
    date = models.DateField()
    first_check_in = models.DateTimeField(null=True, blank=True)
    last_check_out = models.DateTimeField(null=True, blank=True)
    total_hours = models.FloatField(default=0.0)
    regular_hours = models.FloatField(default=0.0)
    overtime_hours = models.FloatField(default=0.0)
    late_minutes = models.IntegerField(default=0)
    early_exit_minutes = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=20, default='present')  # present, absent, half_day, holiday
    
    class Meta:
        db_table = 'daily_attendance'
        indexes = [
            models.Index(fields=['user_id', 'date']),
        ]