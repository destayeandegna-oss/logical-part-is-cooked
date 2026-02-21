from django.utils import timezone
from django.db.models import Q
from datetime import datetime
from .models import AttendanceRecord, DailyAttendance, Assignment, Shift

def update_daily_attendance(user_id, attendance_date):
    """Update or create daily attendance record for a specific user and date"""
    check_in = AttendanceRecord.objects.filter(
        user_id=user_id,
        attendance_type='check_in',
        timestamp__date=attendance_date
    ).order_by('timestamp').first()
    
    check_out = AttendanceRecord.objects.filter(
        user_id=user_id,
        attendance_type='check_out',
        timestamp__date=attendance_date
    ).order_by('-timestamp').first()
    
    if check_in and check_out:
        total_seconds = (check_out.timestamp - check_in.timestamp).total_seconds()
        total_hours = max(0, total_seconds / 3600)
        
        # Calculate overtime (if any)
        assignment = Assignment.objects.filter(
            Q(to_date__gte=attendance_date) | Q(to_date__isnull=True),
            user_id=user_id,
            from_date__lte=attendance_date
        ).first()
        
        overtime_hours = 0
        late_minutes = 0
        
        if assignment:
            try:
                shift = Shift.objects.get(id=assignment.shift_id)
                shift_end_dt = datetime.combine(attendance_date, shift.end_time)
                if timezone.is_aware(check_out.timestamp):
                    shift_end_dt = timezone.make_aware(shift_end_dt)
                
                if check_out.timestamp > shift_end_dt:
                    overtime_seconds = (check_out.timestamp - shift_end_dt).total_seconds()
                    overtime_hours = max(0, overtime_seconds / 3600)

                # Determine late minutes
                if check_in.status == 'late':
                    shift_start_dt = datetime.combine(attendance_date, shift.start_time)
                    if timezone.is_aware(check_in.timestamp):
                        shift_start_dt = timezone.make_aware(shift_start_dt)
                    late_seconds = (check_in.timestamp - shift_start_dt).total_seconds()
                    late_minutes = max(0, int(late_seconds / 60))

            except Shift.DoesNotExist:
                pass
        
        regular_hours = max(0, total_hours - overtime_hours)
        
        # Update or create daily attendance
        DailyAttendance.objects.update_or_create(
            user_id=user_id,
            date=attendance_date,
            defaults={
                'first_check_in': check_in.timestamp,
                'last_check_out': check_out.timestamp,
                'total_hours': total_hours,
                'regular_hours': regular_hours,
                'overtime_hours': overtime_hours,
                'late_minutes': late_minutes,
                'status': 'present'
            }
        )