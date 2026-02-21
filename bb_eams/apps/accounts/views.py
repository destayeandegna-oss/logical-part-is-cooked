from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .models import Department, EmployeeDetail, BiometricTemplate
from .serializers import (
    UserSerializer, UserCreateSerializer, DepartmentSerializer,
    EmployeeDetailSerializer, BiometricTemplateSerializer
)
from apps.core.utils import encrypt_biometric
from .permissions import IsHROfficer

User = get_user_model()

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsHROfficer()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsHROfficer])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Password is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(password)
        user.save()
        
        return Response({'status': 'Password reset successfully'})

class BiometricEnrollmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id')
        biometric_type = request.data.get('biometric_type', 'fingerprint')
        template_data = request.data.get('template_data') # Base64 string
        quality_score = request.data.get('quality_score', 0.0)

        if not all([user_id, template_data]):
            return Response({'error': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            encrypted_data, template_hash = encrypt_biometric(template_data)
            
            BiometricTemplate.objects.create(
                user_id=user_id,
                biometric_type=biometric_type,
                template_data=encrypted_data,
                template_hash=template_hash,
                quality_score=quality_score,
                enrolled_by=request.user.id
            )
            
            # Update user status
            user = User.objects.get(id=user_id)
            user.biometric_enrolled = True
            user.save()
            
            return Response({'status': 'enrolled'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)