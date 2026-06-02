from datetime import timedelta
from django.utils import timezone
from rest_framework.permissions import BasePermission, SAFE_METHODS

class RestrictStaffProductManagement(BasePermission):
    """
    Global Permission: Everyone can view (SAFE_METHODS), 
    but standard staff members are blocked from creating new products.
     Only superusers can issue a POST.
    """
    def has_permission(self, request, view):
        # Allow read-only operations (GET, HEAD, OPTIONS) for anyone
        if request.method in SAFE_METHODS:
            return True
            
        # If trying to create (POST) and user is staff but NOT superuser, block them
        if request.method == 'POST' and request.user.is_staff and not request.user.is_superuser:
            return False
            
        return request.user.is_authenticated


class EditWithinFifteenMinutes(BasePermission):
    """
    Object-Level Permission: A user can only modify (PUT/PATCH) 
    an item if it was created less than 15 minutes ago.
    """
    def has_object_permission(self, request, view, obj):
        # Read operations are always allowed on the instance
        if request.method in SAFE_METHODS:
            return True

        # Ensure the model has a creation timestamp to evaluate against
        if hasattr(obj, 'created_at'):
            execution_window = obj.created_at + timedelta(minutes=15)
            return timezone.now() <= execution_window
            
        return False
    

class IsModerator(BasePermission):
    """
    Role-Based Permission: Brants full access (GET, PUT, PATCH, DELETE)
    to moderators to manage any product, but strictly blocks creation (POST).
    """
    def has_permission(self, request, view):
        # Rule 1: The user must be authenticated and have is_staff=True
        if not (request.user and request.user.is_authenticated and request.user.is_staff):
            return False
        # Rule 3: The moderator cannot create products (POST is prohibited)
        if request.method == 'POST':
            return False
        
        # Rule: 2: Can view, modify, and delete (GET, PUT, PATCH, DELETE are allowed)
        return True