from rest_framework import serializers
from .models import LeaveRequest, LeaveBalance
from datetime import date

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'user_id', 'employee_name', 'leave_type', 'start_date',
            'end_date', 'total_days', 'reason', 'status', 'approved_by',
            'approved_at', 'rejection_reason', 'supporting_documents',
            'created_at', 'remaining_balance'
        ]
        read_only_fields = ['id', 'status', 'approved_by', 'approved_at', 'created_at']
    
    def get_employee_name(self, obj):
        from apps.accounts.models import User
        try:
            user = User.objects.get(id=obj.user_id)
            return user.get_full_name()
        except User.DoesNotExist:
            return None
    
    def get_remaining_balance(self, obj):
        try:
            balance = LeaveBalance.objects.get(
                user_id=obj.user_id,
                year=obj.start_date.year
            )
            if obj.leave_type == 'annual':
                return balance.annual_remaining
            elif obj.leave_type == 'sick':
                return balance.sick_remaining
        except LeaveBalance.DoesNotExist:
            pass
        return None
    
    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        
        # Check for overlapping leave requests
        overlapping = LeaveRequest.objects.filter(
            user_id=data['user_id'],
            status__in=['pending', 'approved'],
            start_date__lte=data['end_date'],
            end_date__gte=data['start_date']
        ).exclude(id=self.instance.id if self.instance else None)
        
        if overlapping.exists():
            raise serializers.ValidationError("Leave request overlaps with existing request")
        
        return data

class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = '__all__'
        read_only_fields = ['id', 'last_updated']

class LeaveApprovalSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if not data['approved'] and not data.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required when rejecting")
        return data