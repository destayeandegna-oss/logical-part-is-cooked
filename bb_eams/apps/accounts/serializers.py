from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Department, EmployeeDetail, BiometricTemplate

User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'employee_id', 'department_id', 'department_name',
            'position', 'phone_number', 'profile_picture', 'status',
            'biometric_enrolled', 'last_login'
        ]
        read_only_fields = ['last_login', 'biometric_enrolled']

    def get_department_name(self, obj):
        if obj.department_id:
            try:
                dept = Department.objects.get(id=obj.department_id)
                return dept.name
            except Department.DoesNotExist:
                pass
        return None

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'user_type', 'employee_id', 'department_id', 'position',
            'phone_number'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class EmployeeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDetail
        fields = '__all__'

class BiometricTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricTemplate
        fields = ['id', 'user_id', 'biometric_type', 'quality_score', 'enrolled_at']
        read_only_fields = ['enrolled_at']