from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date, datetime
from django.db.models import Q
from .models import AttendanceRecord, DailyAttendance, Assignment, Shift
from apps.core.models import Device
from .utils import update_daily_attendance

@shared_task
def sync_offline_attendance():
    """
    Sync offline attendance records from devices
    """
    from apps.accounts.models import User
    
    devices = Device.objects.filter(status='online')
    total_synced = 0
    
    for device in devices:
        try:
            # --- SDK INTEGRATION POINT ---
            # This is where you would connect to your specific biometric device.
            # Example using pyzk:
            # from zk import ZK
            # zk = ZK(device.ip_address, port=device.port, timeout=5)
            # conn = zk.connect()
            # logs = conn.get_attendance()
            # conn.disconnect()
            
            # Mocking logs for structure. Replace 'logs' with actual SDK result.
            logs = [] 
            
            for log in logs:
                # Extract data (adjust attribute names based on your SDK)
                employee_id = getattr(log, 'user_id', None)
                timestamp = getattr(log, 'timestamp', timezone.now())
                punch_type = getattr(log, 'punch', 0) # 0: In, 1: Out
                
                if not employee_id:
                    continue
                    
                # Ensure timestamp is timezone aware
                if timezone.is_naive(timestamp):
                    timestamp = timezone.make_aware(timestamp)

                # Find User
                user = User.objects.filter(employee_id=employee_id).first()
                if not user:
                    continue
                
                # Check for duplicates
                if AttendanceRecord.objects.filter(
                    user_id=user.id, 
                    timestamp=timestamp, 
                    device_id=device.id
                ).exists():
                    continue

                # Determine Type (0/4/5 = Check-In, 1/5 = Check-Out is common)
                attendance_type = 'check_in' if str(punch_type) in ['0', '4', '5'] else 'check_out'
                
                # Determine Status
                status_val = 'on_time'
                log_date = timestamp.date()
                
                assignment = Assignment.objects.filter(
                    Q(to_date__gte=log_date) | Q(to_date__isnull=True),
                    user_id=user.id,
                    from_date__lte=log_date
                ).first()
                
                if assignment:
                    try:
                        shift = Shift.objects.get(id=assignment.shift_id)
                        
                        if attendance_type == 'check_in':
                            shift_start = datetime.combine(log_date, shift.start_time)
                            shift_start = timezone.make_aware(shift_start)
                            grace_end = shift_start + timedelta(minutes=shift.grace_period_minutes)
                            
                            if timestamp > grace_end:
                                status_val = 'late'
                                
                        elif attendance_type == 'check_out':
                            shift_end = datetime.combine(log_date, shift.end_time)
                            shift_end = timezone.make_aware(shift_end)
                            
                            if timestamp < shift_end - timedelta(minutes=30):
                                status_val = 'early_exit'
                            elif timestamp > shift_end:
                                status_val = 'overtime'
                                
                    except Shift.DoesNotExist:
                        pass

                AttendanceRecord.objects.create(
                    user_id=user.id,
                    device_id=device.id,
                    timestamp=timestamp,
                    attendance_type=attendance_type,
                    status=status_val,
                    biometric_verified=True,
                    synced=True
                )
                total_synced += 1

            device.last_communication = timezone.now()
            device.save()
            
        except Exception as e:
            print(f"Error syncing device {device.name}: {e}")
            
    return f"Synced {total_synced} records from {devices.count()} devices"

@shared_task
def calculate_daily_attendance():
    """
    Calculate daily attendance for all employees at end of day
    """
    yesterday = date.today() - timedelta(days=1)
    
    user_ids = AttendanceRecord.objects.filter(
        timestamp__date=yesterday
    ).values_list('user_id', flat=True).distinct()
    
    for user_id in user_ids:
        update_daily_attendance(user_id, yesterday)
    
    return f"Processed {user_ids.count()} users"

@shared_task
def cleanup_old_records():
    """
    Archive or delete old attendance records
    """
    cutoff_date = timezone.now() - timedelta(days=365)
    old_records = AttendanceRecord.objects.filter(timestamp__lt=cutoff_date)
    count = old_records.count()
    old_records.delete()
    return f"Deleted {count} old records"