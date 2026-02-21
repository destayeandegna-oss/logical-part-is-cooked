from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import LeaveRequest
from apps.accounts.models import User

@shared_task
def send_leave_status_email(leave_request_id):
    """
    Sends an email to the employee about their leave request status.
    """
    try:
        leave_request = LeaveRequest.objects.get(id=leave_request_id)
        user = User.objects.get(id=leave_request.user_id)
        
        if leave_request.status == 'approved':
            subject = 'Leave Request Approved'
            message = f"Dear {user.get_full_name()},\n\nYour leave request from {leave_request.start_date} to {leave_request.end_date} has been approved.\n\nRegards,\nHR Department"
        elif leave_request.status == 'rejected':
            subject = 'Leave Request Rejected'
            message = f"Dear {user.get_full_name()},\n\nYour leave request from {leave_request.start_date} to {leave_request.end_date} has been rejected.\nReason: {leave_request.rejection_reason}\n\nRegards,\nHR Department"
        
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
    except (LeaveRequest.DoesNotExist, User.DoesNotExist):
        pass # Or log the error