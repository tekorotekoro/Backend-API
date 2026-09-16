from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Custom permission to only allow superuser to access certain views.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a superuser
        return request.user.is_authenticated and request.user.is_superuser
    
class IsManager(BasePermission):
    """
    Custom permission to only allow managers to access certain views.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a manager
        return request.user.is_authenticated and request.user.groups.filter(name='Manager').exists()
    
class IsDeliveryCrew(BasePermission):
    """
    Custom permission to only allow delivery crew to access certain views.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is a delivery crew member
        return request.user.is_authenticated and request.user.groups.filter(name='Delivery crew').exists()