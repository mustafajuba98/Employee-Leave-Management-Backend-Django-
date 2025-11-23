from rest_framework import permissions


class IsHRUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_hr


class IsOwnerOrHR(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_hr:
            return True
        if hasattr(obj, 'employee') and hasattr(obj.employee, 'user'):
            return obj.employee.user == request.user
        return False


class IsEmployeeOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False

