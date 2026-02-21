from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q, Sum
from datetime import datetime, timedelta, date
from .models import Shift, Assignment, AttendanceRecord, DailyAttendance
from .serializers import (
    ShiftSerializer, AssignmentSerializer, AttendanceRecordSerializer,
    CheckInSerializer, CheckOutSerializer, DailyAttendanceSerializer,
    AttendanceSummarySerializer
)
from apps.core.models import AuditLog, Device
from apps.accounts.models import User
import uuid
from .utils import update_daily_attendance

class CheckInView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        device_id = serializer.validated_data['device_id']
        location_data = serializer.validated_data.get('location_data', {})
        
        # Verify device exists
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's shift for today
        today = date.today()
        assignment = Assignment.objects.filter(
            Q(to_date__gte=today) | Q(to_date__isnull=True),
            user_id=user_id,
            from_date__lte=today
        ).first()
        
        if not assignment:
            return Response(
                {'error': 'No shift assigned for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            shift = Shift.objects.get(id=assignment.shift_id)
        except Shift.DoesNotExist:
            return Response(
                {'error': 'Assigned shift not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determine if late
        check_in_datetime = timezone.now()
        status_type = 'on_time'
        
        shift_start_dt = datetime.combine(today, shift.start_time)
        if timezone.is_aware(check_in_datetime):
            shift_start_dt = timezone.make_aware(shift_start_dt)
        grace_end = shift_start_dt + timedelta(minutes=shift.grace_period_minutes)
        
        if check_in_datetime > grace_end:
            status_type = 'late'
        
        # Create attendance record
        attendance = AttendanceRecord.objects.create(
            user_id=user_id,
            device_id=device_id,
            attendance_type='check_in',
            status=status_type,
            location_data=location_data
        )
        
        # Update device last communication
        device.last_communication = timezone.now()
        device.save()
        
        # Audit log
        AuditLog.objects.create(
            user_id=request.user.id,
            action='check_in',
            resource_type='attendance',
            resource_id=attendance.id,
            description=f"User checked in at {device.name}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Create notification
        from apps.core.models import Notification
        Notification.objects.create(
            user_id=user_id,
            notification_type='success',
            title='Check-In Successful',
            message=f'You checked in at {check_in_datetime.strftime("%H:%M:%S")}',
            status='sent',
            sent_at=timezone.now()
        )
        
        return Response(
            AttendanceRecordSerializer(attendance).data,
            status=status.HTTP_201_CREATED
        )

class CheckOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        device_id = serializer.validated_data['device_id']
        location_data = serializer.validated_data.get('location_data', {})
        
        # Verify device exists
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        today = date.today()
        
        # Get today's check-in
        check_in = AttendanceRecord.objects.filter(
            user_id=user_id,
            attendance_type='check_in',
            timestamp__date=today
        ).first()
        
        # Determine if early exit
        now = timezone.now()
        status_type = 'on_time'
        
        # Get shift end time
        assignment = Assignment.objects.filter(
            Q(to_date__gte=today) | Q(to_date__isnull=True),
            user_id=user_id,
            from_date__lte=today
        ).first()
        
        if assignment:
            try:
                shift = Shift.objects.get(id=assignment.shift_id)
                shift_end_dt = datetime.combine(today, shift.end_time)
                if timezone.is_aware(now):
                    shift_end_dt = timezone.make_aware(shift_end_dt)
                if now < shift_end_dt - timedelta(minutes=30):  # More than 30 min early
                    status_type = 'early_exit'
                elif now > shift_end_dt:
                    status_type = 'overtime'
            except Shift.DoesNotExist:
                pass
        
        # Create checkout record
        checkout = AttendanceRecord.objects.create(
            user_id=user_id,
            device_id=device_id,
            attendance_type='check_out',
            status=status_type,
            location_data=location_data
        )
        
        # Calculate and update daily attendance
        update_daily_attendance(user_id, today)
        
        # Update device
        device.last_communication = timezone.now()
        device.save()
        
        # Audit log
        AuditLog.objects.create(
            user_id=request.user.id,
            action='check_out',
            resource_type='attendance',
            resource_id=checkout.id,
            description=f"User checked out at {device.name}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            AttendanceRecordSerializer(checkout).data,
            status=status.HTTP_201_CREATED
        )

class AttendanceHistoryView(generics.ListAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id', self.request.user.id)
        queryset = AttendanceRecord.objects.filter(user_id=user_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
        
        # Filter by type
        attendance_type = self.request.query_params.get('type')
        if attendance_type:
            queryset = queryset.filter(attendance_type=attendance_type)
        
        return queryset

class DailyAttendanceView(generics.ListAPIView):
    serializer_class = DailyAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = DailyAttendance.objects.all()
        
        # Filter by date
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date=date_param)
        else:
            queryset = queryset.filter(date=timezone.now().date())
        
        # Filter by department
        department_id = self.request.query_params.get('department_id')
        if department_id:
            user_ids = User.objects.filter(department_id=department_id).values_list('id', flat=True)
            queryset = queryset.filter(user_id__in=user_ids)
        
        return queryset

class AttendanceSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        date_param = request.query_params.get('date', timezone.now().date())
        department_id = request.query_params.get('department_id')
        
        # Get all employees
        employees = User.objects.filter(is_active=True, user_type='employee')
        if department_id:
            employees = employees.filter(department_id=department_id)
        
        total_employees = employees.count()
        
        # Get attendance for the date
        attendance = DailyAttendance.objects.filter(date=date_param)
        if department_id:
            attendance = attendance.filter(user_id__in=employees.values_list('id', flat=True))
        
        present = attendance.filter(status='present').count()
        absent = total_employees - present
        
        # Get leave count
        from apps.leave.models import LeaveRequest
        leave_count = LeaveRequest.objects.filter(
            status='approved',
            start_date__lte=date_param,
            end_date__gte=date_param,
            user_id__in=employees.values_list('id', flat=True)
        ).count()
        
        # Late arrivals
        late = attendance.filter(late_minutes__gt=0).count()
        
        summary = {
            'date': date_param,
            'present': present,
            'absent': absent,
            'late': late,
            'on_time': present - late,
            'leave': leave_count,
            'total_employees': total_employees
        }
        
        return Response(AttendanceSummarySerializer(summary).data)

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        department_id = self.request.query_params.get('department_id')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        return queryset