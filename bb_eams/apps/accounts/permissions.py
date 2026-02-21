from rest_framework import permissions

class IsHROfficer(permissions.BasePermission):
    """
    Allows access only to HR officers and Admins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in ['hr_officer', 'admin']