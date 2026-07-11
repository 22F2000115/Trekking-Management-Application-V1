from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_, func
from database import db
from models import User, Trek, Booking
from decorators import staff_required

staff = Blueprint('staff', __name__, url_prefix='/staff')


#* Module Level Constants - Referenced for validation across Staff Routes
STAFF_TREK_STATUSES = ['Bookings Open', 'Bookings Closed', 'Ongoing', 'Completed', 'Cancelled']
PAYMENT_STATUSES = ['Pending', 'Paid', 'Refunded']




# Fetches Assigned Treks For Logged In Staff
def get_assigned_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.assigned_staff_id != current_user.id:
        abort(403)
    return trek


# Fetches Bookings For Assigned Treks For Logged In Staff
def get_assigned_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(403)
    trek = db.session.get(Trek, booking.trek_id)
    if not trek or trek.assigned_staff_id != current_user.id:
        abort(403)
    return booking, trek

# Returns the number of active (Booked) bookings for a trek
def get_active_booking_count(trek_id):
    return db.session.scalar(db.select(func.count(Booking.id)).where(Booking.trek_id == trek_id, Booking.status == 'Booked'))


#! Staff Dashboard

@staff.route('/dashboard')
@staff_required
def dashboard():
    q = request.args.get('q', '').strip()

    base_query = db.select(Trek).where(Trek.assigned_staff_id == current_user.id).order_by(Trek.id.asc())
        # Only Fetched Assigned Treks for Logged In Staff

    if q:
        filters = [Trek.name.ilike(f'%{q}%'), Trek.location.ilike(f'%{q}%'), Trek.status.ilike(f'%{q}%')]
        if q.isdigit():
            filters.append(Trek.id == int(q))
        base_query = base_query.where(or_(*filters))

    trek_list = db.session.execute(base_query).scalars().all()
    
    assigned_treks = db.session.scalar(db.select(func.count(Trek.id)).where(Trek.assigned_staff_id == current_user.id))
    
    total_active_bookings = db.session.scalar(db.select(func.count(Booking.id)).join(Trek, Booking.trek_id == Trek.id).where(Trek.assigned_staff_id == current_user.id, Booking.status == 'Booked'))
    
    bookings_open = db.session.scalar(db.select(func.count(Trek.id)).where(Trek.assigned_staff_id == current_user.id, Trek.status == 'Bookings Open'))

    ongoing_treks = db.session.scalar(db.select(func.count(Trek.id)).where(Trek.assigned_staff_id == current_user.id, Trek.status == 'Ongoing'))


    # Count Only Active Booked Participants (Cancel Bookings Excluded)
    participant_counts = {}
    for trek in trek_list:
        participant_counts[trek.id] = get_active_booking_count(trek.id)

    return render_template('staff/dashboard.html',trek_list = trek_list, participant_counts = participant_counts, assigned_treks = assigned_treks, total_active_bookings = total_active_bookings, bookings_open = bookings_open, ongoing_treks = ongoing_treks, q = q)




#! Trek Detail

#Details for each Trek.
@staff.route('/treks/<int:trek_id>')
@staff_required
def trek_detail(trek_id):
    trek = get_assigned_trek(trek_id)
    
    return render_template('staff/trek_detail.html', trek = trek, staff_trek_statuses = STAFF_TREK_STATUSES)


#Update Trek Status
@staff.route('/treks/<int:trek_id>/status', methods=['POST'])
@staff_required
def update_trek_status(trek_id):
    trek = get_assigned_trek(trek_id)

    new_status = request.form.get('status', '').strip()

    if new_status not in STAFF_TREK_STATUSES:
        flash('Invalid trek status !', 'danger')
        return redirect(url_for('staff.trek_detail', trek_id = trek_id))

    try:
        trek.status = new_status
        
        if new_status in ('Ongoing', 'Completed', 'Cancelled'):
            trek.available_slots = 0
        
        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('Failed to update trek status. Please try again !', 'danger')
        return redirect(url_for('staff.trek_detail', trek_id = trek_id))

    flash(f'Trek status updated to {new_status} !', 'success')
    return redirect(url_for('staff.trek_detail', trek_id = trek_id))


#Update Available Slots (Manual Override)
@staff.route('/treks/<int:trek_id>/slots', methods=['POST'])
@staff_required
def update_slots(trek_id):
    trek = get_assigned_trek(trek_id)

    available_slots = request.form.get('available_slots', '').strip()

    if not available_slots:
        flash('Available slots is required !', 'danger')
        return redirect(url_for('staff.trek_detail', trek_id = trek_id))

    try:
        available_slots = int(available_slots)
    except ValueError:
        flash('Available slots must be a valid number !', 'danger')
        return redirect(url_for('staff.trek_detail', trek_id = trek_id))

    # Maximum Available Slots <= (Total Slots - Active Bookings)
    active_bookings = get_active_booking_count(trek.id)
    max_available_slots = trek.total_slots - active_bookings

    if not (0 <= available_slots <= max_available_slots):
        flash(f'Available slots must be between 0 and {max_available_slots} !', 'danger')
        return redirect(url_for('staff.trek_detail', trek_id=trek.id))

    try:
        trek.available_slots = available_slots
        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('Failed to update slots. Please try again !', 'danger')
        return redirect(url_for('staff.trek_detail', trek_id = trek_id))

    flash('Available slots updated successfully !', 'success')
    return redirect(url_for('staff.trek_detail', trek_id = trek_id))




#! Participants (Trekker Management)

# Fetches Booking Details for Each Trek
@staff.route('/treks/<int:trek_id>/participants')
@staff_required
def participants(trek_id):
    trek = get_assigned_trek(trek_id)

    q = request.args.get('q', '').strip()

    base_query = db.select(Booking).join(User, Booking.user_id == User.id).where(Booking.trek_id == trek_id).order_by(Booking.booked_at.desc())
        # Booking Details for this specific trek only, joined with User for Search (Better UX)

    if q:
        filters = [User.name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%')]
        if q.isdigit():
            filters.append(Booking.id == int(q))
        base_query = base_query.where(or_(*filters))

    booking_list = db.session.execute(base_query).scalars().all()

    return render_template('staff/participants.html', trek = trek, booking_list = booking_list, q = q)


#Cancel Booking (Staff cancelling on behalf of a Trekker / Participant)
    #Note: Once cancelled can't Revert Back
@staff.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@staff_required
def cancel_booking(booking_id):
    booking, trek = get_assigned_booking(booking_id)

    next_url = request.form.get('next', url_for('staff.participants', trek_id = trek.id))
        #* Redirects back to wherever the action was triggered from — Participants or Bookings Page
        
    if trek.status in ('Ongoing', 'Completed', 'Cancelled'):
        flash('Bookings cannot be cancelled once the trek is ongoing, completed, or cancelled.', 'danger')
        return redirect(next_url)

    if booking.status == 'Cancelled':
        flash('This booking is already cancelled !', 'warning')
        return redirect(next_url)

    try:
        booking.status = 'Cancelled'
        trek.available_slots = min(trek.available_slots + 1, trek.total_slots)
            #* Restore slot — capped at total_slots!
            #* Payment Status is intentionally left untouched — All Payments are Managed by Staff
        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('Failed to cancel booking. Please try again !', 'danger')
        return redirect(next_url)

    flash('Booking cancelled successfully. Slot restored !', 'success')
    return redirect(next_url)


#Update Payment Status
@staff.route('/bookings/<int:booking_id>/payment', methods=['POST'])
@staff_required
def update_payment(booking_id):
    booking, trek = get_assigned_booking(booking_id)

    next_url = request.form.get('next', url_for('staff.participants', trek_id = trek.id))

    new_payment_status = request.form.get('payment_status', '').strip()

    if new_payment_status not in PAYMENT_STATUSES:
        flash('Invalid payment status !', 'danger')
        return redirect(next_url)
    
    if booking.payment_status == new_payment_status:
        flash("Payment status is already set!", "info")
        return redirect(next_url)

    try:
        booking.payment_status = new_payment_status
        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('Failed to update payment status. Please try again !', 'danger')
        return redirect(next_url)

    flash(f'Payment status updated to {new_payment_status} !', 'success')
    return redirect(next_url)




#! All Bookings — Flat list across all treks assigned to current staff

@staff.route('/bookings')
@staff_required
def bookings():
    q = request.args.get('q', '').strip()

    base_query = db.select(Booking).join(Trek, Booking.trek_id == Trek.id).join(User, Booking.user_id == User.id).where(Trek.assigned_staff_id == current_user.id).order_by(Booking.booked_at.desc())
        #* Join Booking → Trek → User; filtered to only current staff's assigned treks

    if q:
        filters = [ User.name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%'), Trek.name.ilike(f'%{q}%'), Booking.status.ilike(f'%{q}%'), Booking.payment_status.ilike(f'%{q}%') ]
            #Search by User's Name, Email, Trek Name, Booking Status and Payment Status & Booking ID !
        if q.isdigit():
            filters.append(Booking.id == int(q))
        base_query = base_query.where(or_(*filters))

    booking_list = db.session.execute(base_query).scalars().all()

    return render_template('staff/bookings.html', booking_list = booking_list, q = q)




#! Staff Profile

#Update Profile Info & Update Password
@staff.route('/profile', methods=['GET', 'POST'])
@staff_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_no = request.form.get('contact_no', '').strip()
        bio = request.form.get('bio', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([name, contact_no]):
            flash('Name and contact number are required !', 'danger')
            return render_template('staff/profile.html')

        if not contact_no.isdigit() or len(contact_no) != 10:
            flash('Contact number must be exactly 10 digits !', 'danger')
            return render_template('staff/profile.html')

        change_password = any([current_password, new_password, confirm_password])
            #* Password change is optional — only process if at least one password field is filled

        if change_password:
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect !', 'danger')
                return render_template('staff/profile.html')

            if new_password != confirm_password:
                flash('New passwords do not match !', 'danger')
                return render_template('staff/profile.html')

            if len(new_password) < 8:
                flash('New password must be at least 8 characters !', 'danger')
                return render_template('staff/profile.html')

        try:
            current_user.name = name
            current_user.contact_no = contact_no
            current_user.staff_profile.bio = bio or None

            if change_password:
                current_user.password_hash = generate_password_hash(new_password)

            db.session.commit()

        except Exception:
            db.session.rollback()
            flash('Failed to update profile. Please try again !', 'danger')
            return render_template('staff/profile.html')

        flash('Profile updated successfully !', 'success')
        return redirect(url_for('staff.profile'))

    return render_template('staff/profile.html')