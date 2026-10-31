from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect
from core.constants import UserRole


def role_required(*allowed_roles):
    """
    Decorator for views that checks whether a user has one of the allowed roles.
    Admins are always permitted.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_superuser or request.user.role == UserRole.ADMIN:
                return view_func(request, *args, **kwargs)
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to view this resource.")
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required(UserRole.ADMIN)(view_func)


def staff_required(view_func):
    return role_required(UserRole.ADMIN, UserRole.STAFF)(view_func)


def customer_required(view_func):
    return role_required(UserRole.CUSTOMER)(view_func)
