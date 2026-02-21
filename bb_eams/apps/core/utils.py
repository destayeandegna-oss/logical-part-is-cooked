import hashlib
import base64
import bcrypt
from cryptography.fernet import Fernet
from django.conf import settings
import json
from datetime import datetime, timedelta

def encrypt_biometric(biometric_data):
    """
    Encrypt biometric template data
    """
    # Generate encryption key (in production, use a proper key management system)
    key = settings.BIOMETRIC_TEMPLATE_ENCRYPTION_KEY
    if not key:
        key = Fernet.generate_key()
    
    f = Fernet(key)
    encrypted_data = f.encrypt(biometric_data.encode())
    
    # Generate hash for verification
    template_hash = hashlib.sha256(biometric_data.encode()).hexdigest()
    
    return encrypted_data, template_hash

def verify_biometric(captured_data, stored_encrypted_data):
    """
    Verify captured biometric against stored encrypted template
    """
    try:
        key = settings.BIOMETRIC_TEMPLATE_ENCRYPTION_KEY
        f = Fernet(key)
        decrypted_data = f.decrypt(stored_encrypted_data).decode()
        
        # Compare (simplified - in production use proper biometric matching)
        captured_hash = hashlib.sha256(captured_data.encode()).hexdigest()
        stored_hash = hashlib.sha256(decrypted_data.encode()).hexdigest()
        
        return captured_hash == stored_hash
    except Exception as e:
        return False

def calculate_working_hours(check_in, check_out):
    """
    Calculate working hours between check-in and check-out
    """
    if not check_in or not check_out:
        return 0
    
    delta = check_out - check_in
    hours = delta.total_seconds() / 3600
    return round(hours, 2)

def generate_attendance_report(start_date, end_date, department_id=None):
    """
    Generate attendance report for date range
    """
    from apps.attendance.models import DailyAttendance
    from apps.accounts.models import User
    
    report_data = {
        'period': f"{start_date} to {end_date}",
        'summary': {},
        'details': []
    }
    
    # Get all employees
    employees = User.objects.filter(is_active=True, user_type='employee')
    if department_id:
        employees = employees.filter(department_id=department_id)
    
    # Get attendance records
    attendance = DailyAttendance.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )
    
    if department_id:
        attendance = attendance.filter(user_id__in=employees.values_list('id', flat=True))
    
    # Calculate summary
    total_days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
    report_data['summary']['total_employees'] = employees.count()
    report_data['summary']['total_days'] = total_days
    report_data['summary']['total_attendance'] = attendance.count()
    
    # Employee details
    for employee in employees:
        emp_attendance = attendance.filter(user_id=employee.id)
        total_hours = sum(a.total_hours for a in emp_attendance)
        present_days = emp_attendance.count()
        
        report_data['details'].append({
            'employee_id': str(employee.id),
            'employee_name': employee.get_full_name(),
            'department': employee.department_id,
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'total_hours': round(total_hours, 2),
            'late_days': emp_attendance.filter(late_minutes__gt=0).count()
        })
    
    return report_data