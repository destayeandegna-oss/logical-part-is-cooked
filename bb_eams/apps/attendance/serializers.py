from rest_framework import serializers
from .models import Shift, Assignment, AttendanceRecord, DailyAttendance
from apps.core.models import Device
from django.utils import timezone

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'

class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    device_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'user_id', 'employee_name', 'device_id', 'device_name',
            'timestamp', 'attendance_type', 'status', 'biometric_verified',
            'verification_score', 'location_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_employee_name(self, obj):
        from apps.accounts.models import User
        try:
            user = User.objects.get(id=obj.user_id)
            return user.get_full_name()
        except User.DoesNotExist:
            return None
    
    def get_device_name(self, obj):
        try:
            device = Device.objects.get(id=obj.device_id)
            return device.name
        except Device.DoesNotExist:
            return None

class CheckInSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    device_id = serializers.UUIDField()
    biometric_data = serializers.CharField(required=False)
    location_data = serializers.JSONField(required=False, default=dict)
    
    def validate(self, data):
        # Check if user has already checked in today without checking out
        today = timezone.now().date()
        check_in_exists = AttendanceRecord.objects.filter(
            user_id=data['user_id'],
            attendance_type='check_in',
            timestamp__date=today
        ).exists()
        
        if check_in_exists:
            raise serializers.ValidationError("User already checked in today")
        
        return data

class CheckOutSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    device_id = serializers.UUIDField()
    biometric_data = serializers.CharField(required=False)
    location_data = serializers.JSONField(required=False, default=dict)
    
    def validate(self, data):
        # Check if user has checked in today
        today = timezone.now().date()
        check_in = AttendanceRecord.objects.filter(
            user_id=data['user_id'],
            attendance_type='check_in',
            timestamp__date=today
        ).first()
        
        if not check_in:
            raise serializers.ValidationError("User hasn't checked in today")
        
        # Check if already checked out
        check_out_exists = AttendanceRecord.objects.filter(
            user_id=data['user_id'],
            attendance_type='check_out',
            timestamp__date=today
        ).exists()
        
        if check_out_exists:
            raise serializers.ValidationError("User already checked out today")
        
        return data

class DailyAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyAttendance
        fields = '__all__'
    
    def get_employee_name(self, obj):
        from apps.accounts.models import User
        try:
            user = User.objects.get(id=obj.user_id)
            return user.get_full_name()
        except User.DoesNotExist:
            return None

class AttendanceSummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    on_time = serializers.IntegerField()
    leave = serializers.IntegerField()
    total_employees = serializers.IntegerField()