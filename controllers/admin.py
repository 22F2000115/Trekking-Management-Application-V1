from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_, func
from database import db
from models import User, StaffProfile, Trek, Booking
from decorators import admin_required
from datetime import date
from decimal import Decimal, InvalidOperation

admin = Blueprint('admin', __name__, url_prefix = '/admin')




#! Admin Dashboard

@admin.route('/dashboard')
@admin_required
def dashboard():
    total_users = db.session.scalar(db.select(func.count(User.id)).where(User.role == 'User'))
    total_staff = db.session.scalar(db.select(func.count(User.id)).where(User.role == 'Staff'))
    total_treks = db.session.scalar(db.select(func.count(Trek.id)))
    total_bookings = db.session.scalar(db.select(func.count(Booking.id)))
    pending_staff = db.session.scalar(db.select(func.count(StaffProfile.user_id)).where(StaffProfile.approval_status == 'Pending'))
    
    recent_bookings = db.session.execute(db.select(Booking).order_by(Booking.booked_at.desc()).limit(5)).scalars().all()
        #* Latest 5 Bookings Only    
    
    return render_template('admin/dashboard.html',
        total_users = total_users,
        total_staff = total_staff,
        total_treks = total_treks,
        total_bookings = total_bookings,
        pending_staff = pending_staff,
        recent_bookings = recent_bookings
    )
    





#! Admin's Trek Management

#* Module Level Constants - Referenced for validation across Trek Routes
TREK_STATUSES = ['Pending', 'Approved', 'Bookings Open', 'Bookings Closed', 'Ongoing', 'Completed', 'Cancelled']
TREK_DIFFICULTIES = ['Easy', 'Moderate', 'Hard']
    


#Lists Only Approved and Active Staff
def get_approved_staff():
    return db.session.execute(db.select(User).join(StaffProfile, User.id == StaffProfile.user_id).where(User.role == 'Staff', User.status == 'Active', StaffProfile.approval_status == 'Approved')).scalars().all()

# Returns the number of active (Booked) bookings for a trek
def get_active_booking_count(trek_id):
    return db.session.scalar(db.select(func.count(Booking.id)).where(Booking.trek_id == trek_id, Booking.status == 'Booked'))



#Search Trek / Trek List
@admin.route('/treks')
@admin_required
def treks():
    q = request.args.get('q', '').strip()
    
    base_query = db.select(Trek).order_by(Trek.id.asc())
    
    if q:
        filters = [Trek.name.ilike(f'%{q}%'), Trek.location.ilike(f'%{q}%')]
        if q.isdigit():
            filters.append(Trek.id == int(q))
                #Search by Trek ID when input in Numeric
        base_query = base_query.where(or_(*filters))
    
    trek_list = db.session.execute(base_query).scalars().all()
    approved_staff = get_approved_staff()
    return render_template('admin/treks.html', approved_staff = approved_staff, trek_list = trek_list, trek_statuses=TREK_STATUSES, q = q)



#Add Trek
@admin.route('/treks/add', methods = ['GET', 'POST'])
@admin_required
def add_trek():
    
    approved_staff = get_approved_staff()       #Helper to get only Approved and Active Staff
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        duration = request.form.get('duration', '').strip()
        price = request.form.get('price', '').strip()
        total_slots = request.form.get('total_slots', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        description = request.form.get('description', '').strip()
        staff_id = request.form.get('assigned_staff_id', '').strip()
            #Trek may be created without an assigned staff member.
        
        if not all([name, location, difficulty, duration, price, total_slots, start_date, end_date]):
            flash('All fields except description and assigned staff are required !', 'danger')
            return render_template('admin/add_trek.html', approved_staff = approved_staff)
        
        if difficulty not in TREK_DIFFICULTIES:
            flash('Invalid difficulty level !', 'danger')
            return render_template('admin/add_trek.html', approved_staff = approved_staff)
        
        try:
            duration = int(duration)
            total_slots = int(total_slots)
            price = Decimal(price)      #Decimal matches Numeric(10,2) in DB
        except (ValueError, InvalidOperation):
            flash('Duration, slots, and price must be valid numbers !', 'danger')
            return render_template('admin/add_trek.html', approved_staff = approved_staff)
        
        if duration <= 0 or total_slots <= 0 or price < 0:
            flash('Duration and slots must be positive. Price cannot be negative!', 'danger')
            return render_template('admin/add_trek.html', approved_staff = approved_staff)
        
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError:
            flash('Invalid date format !', 'danger')
            return render_template('admin/add_trek.html', approved_staff = approved_staff)
        
        if end <= start:
            flash('End date must be after start date!', 'danger')
            return render_template('admin/add_trek.html', approved_staff = approved_staff)
        
        assigned_staff_id = int(staff_id) if staff_id.isdigit() else None
            # Unassigned trek allowed
        
        if assigned_staff_id is not None:
            approved_staff_ids = {staff.id for staff in approved_staff}
    
            if assigned_staff_id not in approved_staff_ids:
                flash('Invalid staff selection !', 'danger')
                return render_template('admin/add_trek.html', approved_staff = approved_staff)
        
        try:
            trek = Trek(
                name = name,
                location = location,
                difficulty = difficulty,
                duration = duration,
                price = price,
                total_slots = total_slots,
                available_slots = total_slots,      #Trek starts with all total slots!
                assigned_staff_id = assigned_staff_id,
                status = 'Pending',
                start_date = start,
                end_date = end,
                description = description or None
            )
            
            db.session.add(trek)
            db.session.commit()
        
        except Exception:
            db.session.rollback()
            flash('Failed to create trek. Please try again !', 'danger')
            return render_template('admin/add_trek.html', approved_staff = approved_staff)
        
        flash('Trek created successfully!', 'success')
        return redirect(url_for('admin.treks'))
    
    return render_template('admin/add_trek.html', approved_staff = approved_staff, trek_difficulties = TREK_DIFFICULTIES)



#Edit Trek
@admin.route('/treks/<int:trek_id>/edit', methods = ['GET', 'POST'])
@admin_required
def edit_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        flash('Trek not found !', 'danger')
        return redirect(url_for('admin.treks'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        duration = request.form.get('duration', '').strip()
        price = request.form.get('price', '').strip()
        total_slots = request.form.get('total_slots', '').strip()
        available_slots = request.form.get('available_slots', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        description = request.form.get('description', '').strip()
            #Staff Assignment is intentionally Excluded — Handled exclusively by assign_staff()
        
        if not all([name, location, difficulty, duration, price, total_slots, available_slots, start_date, end_date]):
            flash('All fields except description are required !', 'danger')
            return render_template('admin/edit_trek.html', trek = trek)
        
        if difficulty not in TREK_DIFFICULTIES:
            flash('Invalid difficulty level !', 'danger')
            return render_template('admin/edit_trek.html', trek = trek)
        
        try:
            duration = int(duration)
            total_slots = int(total_slots)
            available_slots = int(available_slots)
            price = Decimal(price)      #Decimal matches Numeric(10,2) in DB
        except (ValueError, InvalidOperation):
            flash('Duration, slots, and price must be valid numbers !', 'danger')
            return render_template('admin/edit_trek.html', trek = trek)
        
        if duration <= 0 or total_slots <= 0 or price < 0:
            flash('Duration and slots must be positive. Price cannot be negative!', 'danger')
            return render_template('admin/edit_trek.html', trek = trek)
        
        # Total Slots can't be updated less than Active Bookings!
        active_bookings = get_active_booking_count(trek.id)
        
        if total_slots < active_bookings:
            flash(f'Total slots cannot be less than the {active_bookings} active bookings!', 'danger')
            return render_template('admin/edit_trek.html', trek=trek)   
        
        # Available Slots <= (Total Slots - Active Bookings)
        max_available_slots = total_slots - active_bookings
        
        if not (0 <= available_slots <= max_available_slots):
            flash(f'Available slots must be between 0 and {max_available_slots} !', 'danger')
            return render_template('admin/edit_trek.html', trek=trek)
        
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError:
            flash('Invalid date format!', 'danger')
            return render_template('admin/edit_trek.html', trek = trek)
        
        if end <= start:
            flash('End date must be after start date !', 'danger')
            return render_template('admin/edit_trek.html', trek = trek)
        
        try:
            trek.name = name
            trek.location = location
            trek.difficulty = difficulty
            trek.duration = duration
            trek.price = price
            trek.total_slots = total_slots
            trek.available_slots = available_slots
            trek.start_date = start
            trek.end_date = end
            trek.description = description or None
            
            db.session.commit()
        
        except Exception:
            db.session.rollback()
            flash('Failed to update trek. Please try again !', 'danger')
            return render_template('admin/edit_trek.html', trek = trek)
        
        flash('Trek updated successfully!', 'success')
        return redirect(url_for('admin.treks'))
    
    return render_template('admin/edit_trek.html', trek = trek, trek_difficulties = TREK_DIFFICULTIES)



#Assign / Reassign and Unassign Staff
@admin.route('/treks/<int:trek_id>/assign-staff', methods = ['POST'])
@admin_required
def assign_staff(trek_id):
    trek = db.session.get(Trek, trek_id)
    
    if not trek:
        flash('Trek not found !', 'danger')
        return redirect(url_for('admin.treks'))
    
    if trek.status in ('Ongoing', 'Completed', 'Cancelled'):
        flash('Cannot reassign staff once a trek is ongoing, completed or cancelled !', 'danger')
        return redirect(url_for('admin.treks'))
    
    approved_staff = get_approved_staff()
    
    staff_id = request.form.get('assigned_staff_id', '').strip()
    assigned_staff_id = int(staff_id) if staff_id.isdigit() else None
    
    if assigned_staff_id is not None:
        approved_staff_ids = {staff.id for staff in approved_staff}
            
        if assigned_staff_id not in approved_staff_ids:
            flash('Invalid staff selection !', 'danger')
            return redirect(url_for('admin.treks'))
    
    try:
        trek.assigned_staff_id = assigned_staff_id
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Failed to update staff assignment. Please try again !', 'danger')
        return redirect(url_for('admin.treks'))
    
    flash('Staff assignment updated successfully!', 'success')
    return redirect(url_for('admin.treks'))
    


#Delete trek
@admin.route('/treks/<int:trek_id>/delete', methods = ['POST'])
@admin_required
def delete_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    
    if not trek:
        flash('Trek not found !', 'danger')
        return redirect(url_for('admin.treks'))
    
    has_bookings = db.session.scalar(db.select(Booking.id).where(Booking.trek_id == trek_id).limit(1))
        #Fetches only one booking if booking exists
    
    if has_bookings:
        flash("Can't delete a trek with existing bookings!", 'danger')
            #Preserves Booking History -  Can't delete Trek if it has bookings already
        return redirect(url_for('admin.treks'))
    
    try:
        db.session.delete(trek)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Failed to delete trek. Please try again !', 'danger')
        return redirect(url_for('admin.treks'))
    
    flash('Trek deleted successfully !', 'success')
    return redirect(url_for('admin.treks'))



#Update Trek Status (Admin can set 'trek.status' to any Valid Status from TREK_STATUSES)
@admin.route('/treks/<int:trek_id>/status', methods = ['POST'])
@admin_required
def update_trek_status(trek_id):
    trek = db.session.get(Trek, trek_id)
    
    if not trek:
        flash('Trek not found !', 'danger')
        return redirect(url_for('admin.treks'))
    
    new_status = request.form.get('status', '').strip()
    if new_status not in TREK_STATUSES:
        flash('Invalid trek status !', 'danger')
        return redirect(url_for('admin.treks'))
    
    try:
        trek.status = new_status

        if new_status in ("Ongoing", "Completed", "Cancelled"):
            trek.available_slots = 0

        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Failed to update trek status. Please try again !', 'danger')
        return redirect(url_for('admin.treks'))
    
    flash(f'Trek status updated to {new_status} !', 'success')
    return redirect(url_for('admin.treks'))





#! Admin's Staff Management

# Staff Search / Staff List
@admin.route('/staff')
@admin_required
def staff():
    q = request.args.get('q', '').strip()
    
    base_query = db.select(User).join(StaffProfile, User.id == StaffProfile.user_id).where(User.role == 'Staff').order_by(User.name)
    
    if q:
        filters = [User.name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%'), StaffProfile.approval_status.ilike(f'%{q}%')]
            #Search by Name, Email, Approval Status in filters currently
        if q.isdigit():
            filters.append(User.id == int(q))
            
        base_query = base_query.where(or_(*filters))
    
    staff_list = db.session.execute(base_query).scalars().all()
    return render_template('admin/staff.html', staff_list = staff_list, q = q)



#Approve Staff
@admin.route('/staff/<int:user_id>/approve', methods = ['POST'])
@admin_required
def approve_staff(user_id):
    user = db.session.get(User, user_id)
    
    if not user or user.role != 'Staff' or user.staff_profile is None:
        flash('Staff member not found !', 'danger')
        return redirect(url_for('admin.staff'))
    
    if user.status == 'Blacklisted':
        flash(f'{user.name} is blacklisted. Activate the account before approving!', 'warning')
        return redirect(url_for('admin.staff'))
    
    if user.staff_profile.approval_status == 'Approved':
        flash(f'{user.name} has already been approved !', 'warning')
        return redirect(url_for('admin.staff'))
    
    try:
        user.staff_profile.approval_status = 'Approved'
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        flash('Approval failed. Please try again !', 'danger')
        return redirect(url_for('admin.staff'))
    
    flash(f'{user.name} approved as a Staff successfully !', 'success')
    return redirect(url_for('admin.staff'))



#Reject Staff
@admin.route('/staff/<int:user_id>/reject', methods = ['POST'])
@admin_required
def reject_staff(user_id):
    user = db.session.get(User, user_id)
    
    if not user or user.role != 'Staff' or user.staff_profile is None:
        flash('Staff member not found !', 'danger')
        return redirect(url_for('admin.staff'))
    
    if user.status == 'Blacklisted':
        flash(f'{user.name} is blacklisted. Activate the account before rejecting!', 'warning')
        return redirect(url_for('admin.staff'))
    
    if user.staff_profile.approval_status == 'Rejected':
        flash(f'{user.name} has already been rejected !', 'warning')
        return redirect(url_for('admin.staff'))
    
    try:
        user.staff_profile.approval_status = 'Rejected'
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        flash('Rejection failed. Please try again !', 'danger')
        return redirect(url_for('admin.staff'))
    
    flash(f'{user.name} has been rejected as a Staff successfully !', 'success')
    return redirect(url_for('admin.staff'))



#Blacklist Staff
@admin.route('/staff/<int:user_id>/blacklist', methods = ['POST'])
@admin_required
def blacklist_staff(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != 'Staff':
        flash('Staff member not found !', 'danger')
        return redirect(url_for('admin.staff'))
    
    if user.status == 'Blacklisted':
        flash(f'{user.name} is already blacklisted !', 'warning')
        return redirect(url_for('admin.staff'))
    
    assigned_treks = db.session.execute(db.select(Trek).where(Trek.assigned_staff_id == user.id, Trek.status.not_in(('Ongoing', 'Completed', 'Cancelled')))).scalars().all()
        #Fetches all the treks where Trek.status != 'Ongoing' / 'Completed' / 'Cancelled' ; If Trek.status == 'Ongoing' / 'Completed' / 'Cancelled' - assigned staff won't be unassigned.
    
    try:
        user.status = 'Blacklisted'
        user.staff_profile.approval_status = 'Rejected'
        for trek in assigned_treks:
            trek.assigned_staff_id = None
            
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        flash('Blacklist failed. Please try again !', 'danger')
        return redirect(url_for('admin.staff'))
    
    flash(f'{user.name} has been blacklisted and unassigned from applicable treks !', 'warning')
    return redirect(url_for('admin.staff'))



#Activate Staff
@admin.route('/staff/<int:user_id>/activate', methods = ['POST'])
@admin_required
def activate_staff(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != 'Staff':
        flash('Staff member not found !', 'danger')
        return redirect(url_for('admin.staff'))
    
    if user.status == 'Active':
        flash(f'{user.name} is already Active !', 'warning')
        return redirect(url_for('admin.staff'))
    
    try:
        user.status = 'Active'
        user.staff_profile.approval_status = 'Pending'
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        flash('Activation failed. Please try again !', 'danger')
        return redirect(url_for('admin.staff'))
    
    flash(f'{user.name} has been reactivated successfully !', 'success')
    return redirect(url_for('admin.staff'))





#! Admin's User Management

#Search Users / Users List
@admin.route('/users')
@admin_required
def users():
    q = request.args.get('q', '').strip()
    
    base_query = db.select(User).where(User.role == 'User').order_by(User.name)
    
    if q:
        filters = [User.name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%')]
        if q.isdigit():
            filters.append(User.id == int(q))
        base_query = base_query.where(or_(*filters))
    
    user_list = db.session.execute(base_query).scalars().all()
    return render_template('admin/users.html', user_list = user_list, q = q)



#Blacklist Users
@admin.route('/users/<int:user_id>/blacklist', methods = ['POST'])
@admin_required
def blacklist_user(user_id):
    user = db.session.get(User, user_id)
    
    if not user or user.role != 'User':
        flash('User not found !', 'danger')
        return redirect(url_for('admin.users'))
    
    if user.status == 'Blacklisted':
        flash(f'{user.name} is already blacklisted !', 'warning')
        return redirect(url_for('admin.users'))
    
    try:
        user.status = 'Blacklisted'
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        flash('Blacklist failed. Please try again !', 'danger')
        return redirect(url_for('admin.users'))
    
    flash(f'{user.name} has been blacklisted successfully !', 'warning')
    return redirect(url_for('admin.users'))



#Activate Users
@admin.route('/users/<int:user_id>/activate', methods = ['POST'])
@admin_required
def activate_user(user_id):
    user = db.session.get(User, user_id)
    if not user or user.role != 'User':
        flash('User not found !', 'danger')
        return redirect(url_for('admin.users'))
    
    if user.status == 'Active':
        flash(f'{user.name} is already Active !', 'warning')
        return redirect(url_for('admin.users'))
    
    try:
        user.status = 'Active'
        db.session.commit()
        
    except Exception:
        db.session.rollback()
        flash('Activation failed. Please try again !', 'danger')
        return redirect(url_for('admin.users'))
    
    flash(f'{user.name} has been reactivated successfully !', 'success')
    return redirect(url_for('admin.users'))





#! Admin's Booking View

@admin.route('/bookings')
@admin_required
def bookings():
    q = request.args.get('q', '').strip()

    base_query = db.select(Booking).join(User, Booking.user_id == User.id).join(Trek, Booking.trek_id == Trek.id).order_by(Booking.booked_at.desc())

    if q:
        filters = [User.name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%'), Trek.name.ilike(f'%{q}%'), Booking.status.ilike(f'%{q}%'), Booking.payment_status.ilike(f'%{q}%')]
            #Search by Name, Email, Trek Name, Booking Status and Payment Status!
        if q.isdigit():
            filters.append(Booking.id == int(q))

        base_query = base_query.where(or_(*filters))

    booking_list = db.session.execute(base_query).scalars().all()
    return render_template('admin/bookings.html', booking_list=booking_list, q=q)