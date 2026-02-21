from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import LeaveRequest, LeaveBalance
from .serializers import (
    LeaveRequestSerializer, LeaveBalanceSerializer,
    LeaveApprovalSerializer
)
from apps.core.models import AuditLog, Notification
from .tasks import send_leave_status_email
import uuid

class LeaveRequestListView(generics.ListCreateAPIView):
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        
        if user_id:
            queryset = LeaveRequest.objects.filter(user_id=user_id)
        else:
            # HR and admin can see all
            if self.request.user.user_type in ['admin', 'hr_officer']:
                queryset = LeaveRequest.objects.all()
            else:
                queryset = LeaveRequest.objects.filter(user_id=self.request.user.id)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        leave_request = serializer.save(user_id=self.request.user.id)
        
        # Audit log
        AuditLog.objects.create(
            user_id=self.request.user.id,
            action='leave_request',
            resource_type='leave_request',
            resource_id=leave_request.id,
            description=f"Leave request created for {leave_request.total_days} days",
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        # Notify HR officers
        from apps.accounts.models import User
        hr_officers = User.objects.filter(user_type='hr_officer', is_active=True)
        for hr in hr_officers:
            Notification.objects.create(
                user_id=hr.id,
                notification_type='info',
                title='New Leave Request',
                message=f"{self.request.user.get_full_name()} requested {leave_request.total_days} days {leave_request.leave_type} leave",
                status='pending'
            )

class LeaveRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        old_data = LeaveRequestSerializer(self.get_object()).data
        serializer.save()
        new_data = serializer.data
        
        AuditLog.objects.create(
            user_id=self.request.user.id,
            action='update',
            resource_type='leave_request',
            resource_id=self.get_object().id,
            description=f"Leave request updated",
            old_values=old_data,
            new_values=new_data,
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

class LeaveApprovalView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        # Check permission
        if request.user.user_type not in ['admin', 'hr_officer']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            leave_request = LeaveRequest.objects.get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response(
                {'error': 'Leave request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LeaveApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        approved = serializer.validated_data['approved']
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        if approved:
            # Check leave balance
            try:
                balance = LeaveBalance.objects.get(
                    user_id=leave_request.user_id,
                    year=leave_request.start_date.year
                )
            except LeaveBalance.DoesNotExist:
                # Create balance if not exists
                balance = LeaveBalance.objects.create(
                    user_id=leave_request.user_id,
                    year=leave_request.start_date.year
                )
            
            # Check available balance
            if leave_request.leave_type == 'annual':
                if balance.annual_remaining < leave_request.total_days:
                    return Response(
                        {'error': 'Insufficient annual leave balance'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                balance.annual_used += leave_request.total_days
                balance.annual_remaining -= leave_request.total_days
            elif leave_request.leave_type == 'sick':
                if balance.sick_remaining < leave_request.total_days:
                    return Response(
                        {'error': 'Insufficient sick leave balance'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                balance.sick_used += leave_request.total_days
                balance.sick_remaining -= leave_request.total_days
            
            balance.save()
            
            leave_request.status = 'approved'
            leave_request.approved_by = request.user.id
            leave_request.approved_at = timezone.now()
            
            notification_message = f"Your {leave_request.leave_type} leave request for {leave_request.total_days} days has been approved"
        else:
            leave_request.status = 'rejected'
            leave_request.rejection_reason = rejection_reason
            notification_message = f"Your {leave_request.leave_type} leave request has been rejected: {rejection_reason}"
        
        leave_request.save()
        
        # Trigger email notification task
        send_leave_status_email.delay(leave_request.id)
        
        # Notify employee
        Notification.objects.create(
            user_id=leave_request.user_id,
            notification_type='success' if approved else 'error',
            title=f'Leave Request {leave_request.status.title()}',
            message=notification_message,
            status='pending'
        )
        
        # Audit log
        AuditLog.objects.create(
            user_id=request.user.id,
            action='approve' if approved else 'reject',
            resource_type='leave_request',
            resource_id=leave_request.id,
            description=f"Leave request {leave_request.status}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(LeaveRequestSerializer(leave_request).data)

class LeaveBalanceView(generics.RetrieveAPIView):
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user_id = self.request.query_params.get('user_id', self.request.user.id)
        year = self.request.query_params.get('year', timezone.now().year)
        
        try:
            balance = LeaveBalance.objects.get(user_id=user_id, year=year)
        except LeaveBalance.DoesNotExist:
            balance = LeaveBalance.objects.create(user_id=user_id, year=year)
        
        return balance