from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, StaffProfile

auth = Blueprint('auth', __name__, url_prefix = '/auth')


def is_valid_contact(contact_no):
    return contact_no.isdigit() and len(contact_no) == 10
        # 10 digits exactly — suits Indian phone numbers

#* Redirects users to their respective dashboards based on their role.
def redirect_user_by_role(user):
    if user.role == 'Admin':
        return redirect(url_for('admin.dashboard'))
    
    if user.role == 'Staff':
        if user.staff_profile is None:
            abort(403)
        
        if user.staff_profile.approval_status == 'Pending':
            return render_template('staff/pending.html')
        
        if user.staff_profile.approval_status == 'Rejected':
            logout_user()   # Always log out first if approval was rejected.
            flash('Your staff application has been rejected. Contact admin.', 'danger')
            abort(403)
        
        if user.staff_profile.approval_status == 'Approved':
            return redirect(url_for('staff.dashboard'))
        
        abort(403)
            # Unknown approval status — defensive fallback.
            
    if user.role == 'User':
        return redirect(url_for('user.dashboard'))
    
    abort(403)



#! Register User

@auth.route('/register/user', methods = ['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect_user_by_role(current_user)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
            # Normalize — prevents duplicate accounts with different casing
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        contact_no = request.form.get('contact_no', '').strip()
        
        if not all ([name, email, password, confirm_password, contact_no]):
            flash('All fields are required!', 'danger')
            return render_template('auth/register_user.html')
        
        if password != confirm_password:
            flash('The passwords entered do not match. Please try again.', 'danger')
            return render_template('auth/register_user.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters!', 'danger')
            return render_template('auth/register_user.html')
        
        if not is_valid_contact(contact_no):
            flash('Contact number must be exactly 10 digits!', 'danger')
            return render_template('auth/register_user.html')
        
        existing_user =  db.session.execute(db.select(User).filter_by(email = email)).scalar_one_or_none()
        if existing_user:
            flash('Email already registered. Please use another email!', 'danger')
            return render_template('auth/register_user.html')
        
        try:
            user = User(
                name = name,
                email = email,
                password_hash = generate_password_hash(password),
                contact_no = contact_no,
                role = 'User',
                status = 'Active'
            )
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Registration failed. Please try again!', 'danger')
            return render_template('auth/register_user.html')
        
        
        flash('Account created. Please log in!','success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register_user.html')


#! Register Staff

@auth.route('/register/staff', methods = ['GET', 'POST'])
def register_staff():
    if current_user.is_authenticated:
        return redirect_user_by_role(current_user)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
            # Normalize — prevents duplicate accounts with different casing
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        contact_no = request.form.get('contact_no', '').strip()
        bio = request.form.get('bio', '').strip()
            # Optional — db.Text, nullable
            
        if not all([name, email, password, confirm_password, contact_no]):
            flash('All fields except bio are required!', 'danger')
            return render_template('auth/register_staff.html')
        
        if password != confirm_password:
            flash('The passwords entered do not match. Please try again.', 'danger')
            return render_template('auth/register_staff.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters!', 'danger')
            return render_template('auth/register_staff.html')
        
        if not is_valid_contact(contact_no):
            flash('Contact number must be exactly 10 digits!', 'danger')
            return render_template('auth/register_staff.html')
        
        existing_user = db.session.execute(db.select(User).filter_by(email = email)).scalar_one_or_none()
        if existing_user:
            flash('Email already registered. Please use another email!', 'danger')
            return render_template('auth/register_staff.html')
        
        
        try:
            user = User(
                name = name,
                email = email,
                password_hash = generate_password_hash(password),
                contact_no = contact_no,
                role = 'Staff',
                status = 'Active'
            )
            
            db.session.add(user)
            db.session.flush()
                # flush assigns user.id from DB without committing — needed for StaffProfile FK
                
                
            staff_profile = StaffProfile(
                user_id = user.id,
                bio = bio or None,
                    # Empty string → None to keep DB clean
                approval_status = 'Pending'
            )
            db.session.add(staff_profile)
            db.session.commit()
                # Both User and StaffProfile committed in one transaction
        
        except Exception:
            db.session.rollback()
            flash('Registration failed. Please try again!', 'danger')
            return render_template('auth/register_staff.html')
        
        flash("Staff account created. Requires Admin's approval.", 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register_staff.html')



#! Main Login

@auth.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_user_by_role(current_user)
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
            # Normalize — matches stored lowercase email
        password = request.form.get('password', '')
        
        if not all ([email, password]):
            flash('Email and password are required!', 'danger')
            return render_template('auth/login.html')
        
        existing_user = db.session.execute(db.select(User).filter_by(email = email)).scalar_one_or_none()
        
        if not existing_user or not check_password_hash(existing_user.password_hash, password):
            # Intentional Authentication Ambiguity
            flash('Invalid Credentials!', 'danger')
            return render_template('auth/login.html')
        
        if existing_user.role != 'Admin' and existing_user.status == 'Blacklisted':
            # Admin can never be blacklisted — check skipped for Admin
            flash('Your account has been blacklisted. Please Contact Admin!', 'danger')
            abort(403)
        
        login_user(existing_user)
        return redirect_user_by_role(existing_user)
    
    return render_template('auth/login.html')



#! Logout User

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))