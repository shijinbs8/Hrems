 # myapp/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def superuser_or_senior_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        # Check both conditions
        if user.is_authenticated and (user.is_superuser or getattr(user, "employeeprofile", None) and getattr(user.employeeprofile, "is_senior", False)):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "You do not have permission to access this page.")
            return redirect("no_permission")  # Replace with your desired redirect page name
    return _wrapped_view
