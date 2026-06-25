from functools import wraps
    # Preserves original function name — prevents Flask route naming conflicts.
from flask import abort, redirect, url_for
    # abort — Triggers custom 403 handler, redirect, url_for — Sends unauthenticated users to login.
from flask_login import current_user
    # Logged-in user object.
    
    
def admin_required(func):
    #* Admin-only access.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'Admin':
            abort(403)
        return func(*args, **kwargs)
    return wrapper



def staff_required(func):
    #* Active, Approved Staff only.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'Staff':
            abort(403)
        if current_user.status != 'Active':
            abort(403)
        if current_user.staff_profile is None:
            abort(403)
            # Role set but StaffProfile never created — broken registration.
        if current_user.staff_profile.approval_status == 'Pending':
            return redirect(url_for('staff.pending'))
        if current_user.staff_profile.approval_status == 'Rejected':
            abort(403)
        if current_user.staff_profile.approval_status != 'Approved':
            abort(403)
        return func(*args, **kwargs)
    return wrapper



def user_required(func):
    #* Active Users only.
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'User':
            abort(403)
        if current_user.status != 'Active':
            abort(403)
        return func(*args, **kwargs)
    return wrapper