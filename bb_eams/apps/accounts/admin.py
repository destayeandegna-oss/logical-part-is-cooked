from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Department, EmployeeDetail, BiometricTemplate

class DepartmentFilter(admin.SimpleListFilter):
    title = 'department'
    parameter_name = 'department_id'

    def lookups(self, request, model_admin):
        departments = Department.objects.all()
        return [(str(dept.id), dept.name) for dept in departments]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(department_id=self.value())
        return queryset

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'get_department', 'status')
    list_filter = ('user_type', 'status', DepartmentFilter, 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        ('Employment', {'fields': ('user_type', 'employee_id', 'department_id', 'position', 'status', 'hire_date')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    readonly_fields = ('created_at', 'last_login')

    def get_department(self, obj):
        if obj.department_id:
            try:
                return Department.objects.get(id=obj.department_id).name
            except Department.DoesNotExist:
                return None
        return '-'
    get_department.short_description = 'Department'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

admin.site.register(EmployeeDetail)
admin.site.register(BiometricTemplate)