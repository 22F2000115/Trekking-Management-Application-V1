from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_, func
from database import db
from models import User, Trek, Booking
from decorators import user_required

user = Blueprint('user', __name__, url_prefix = '/user')


#* Module Level Constants - Referenced for validation across User Routes
TREK_DIFFICULTIES = ['Easy', 'Moderate', 'Hard']
USER_VISIBLE_TREKS = ['Approved', 'Bookings Open']
BOOKABLE_STATUS = 'Bookings Open'
    #* Only 'Bookings Open' treks can be booked — 'Approved' is visible but not bookable




#! User Dashboard

@user.route('/dashboard')
@user_required
def dashboard():
    # 4 Stat Cards
    active_bookings = db.session.scalar(db.select(func.count(Booking.id)).where(Booking.user_id == current_user.id, Booking.status == 'Booked'))

    open_treks = db.session.scalar(db.select(func.count(Trek.id)).where(Trek.status == 'Bookings Open'))

    approved_treks = db.session.scalar(db.select(func.count(Trek.id)).where(Trek.status == 'Approved'))

    completed_treks = db.session.scalar(db.select(func.count(Booking.id)).join(Trek, Booking.trek_id == Trek.id).where(Booking.user_id == current_user.id, Booking.status == 'Booked', Trek.status == 'Completed'))

    #Last 3 Active Booked Treks
    active_trek_bookings = db.session.execute(db.select(Booking).join(Trek, Booking.trek_id == Trek.id).where(Booking.user_id == current_user.id, Booking.status == 'Booked').order_by(Booking.booked_at.desc()).limit(3)).scalars().all()

    #Recent 5 Bookings
    recent_bookings = db.session.execute(db.select(Booking).where(Booking.user_id == current_user.id).order_by(Booking.booked_at.desc()).limit(5)).scalars().all()

    return render_template('user/dashboard.html', active_bookings = active_bookings, open_treks = open_treks, approved_treks = approved_treks, completed_treks = completed_treks, active_trek_bookings = active_trek_bookings, recent_bookings = recent_bookings)




#! Trek Browsing

#Browse / Search / Filter Treks
@user.route('/treks')
@user_required
def treks():
    q = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '').strip()

    base_query = db.select(Trek).where(Trek.status.in_(USER_VISIBLE_TREKS)).order_by(Trek.start_date.asc())
        #* 'Approved' and 'Bookings' Open treks are visible to users But Only 'Bookings Open' Treks can be Booked

    if q:
        filters = [Trek.name.ilike(f'%{q}%'), Trek.location.ilike(f'%{q}%')]
            #Search by trek name or location
        base_query = base_query.where(or_(*filters))

    if difficulty and difficulty in TREK_DIFFICULTIES:
        base_query = base_query.where(Trek.difficulty == difficulty)

    trek_list = db.session.execute(base_query).scalars().all()
    return render_template('user/treks.html', trek_list = trek_list, trek_difficulties = TREK_DIFFICULTIES, q = q, selected_difficulty = difficulty)



#Trek Detail
@user.route('/treks/<int:trek_id>')
@user_required
def trek_detail(trek_id):
    trek = db.session.get(Trek, trek_id)

    if not trek or trek.status not in USER_VISIBLE_TREKS:
        flash('Trek not found !', 'danger')
        return redirect(url_for('user.treks'))

    existing_booking = db.session.execute(db.select(Booking).where(Booking.user_id == current_user.id, Booking.trek_id == trek_id, Booking.status == 'Booked')).scalar_one_or_none()
        #* Check if user already has an active booking for this trek — drives button state in template !

    return render_template('user/trek_detail.html', trek = trek, existing_booking = existing_booking)




#! Booking

#Book a Trek
@user.route('/treks/<int:trek_id>/book', methods = ['POST'])
@user_required
def book_trek(trek_id):
    trek = db.session.get(Trek, trek_id)

    if not trek:
        flash('Trek not found !', 'danger')
        return redirect(url_for('user.treks'))

    if trek.status != BOOKABLE_STATUS:
        flash('This trek is not open for bookings !', 'danger')
        return redirect(url_for('user.trek_detail', trek_id = trek_id))

    #* No duplicate active booking for same user and trek !
    existing_booking = db.session.execute(db.select(Booking).where(Booking.user_id == current_user.id, Booking.trek_id == trek_id, Booking.status == 'Booked')).scalar_one_or_none()

    if existing_booking:
        flash('You have already booked this trek !', 'warning')
        return redirect(url_for('user.trek_detail', trek_id = trek_id))

    if trek.available_slots <= 0:
        flash('No slots available for this trek !', 'danger')
        return redirect(url_for('user.trek_detail', trek_id = trek_id))

    try:
        booking = Booking(
            user_id = current_user.id,
            trek_id = trek_id,
            status = 'Booked',
            payment_status = 'Pending'
        )

        db.session.add(booking)
        trek.available_slots -= 1
            #* Decrement slot atomically within the same transaction!

        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('Booking failed. Please try again !', 'danger')
        return redirect(url_for('user.trek_detail', trek_id = trek_id))

    flash('Trek booked successfully !', 'success')
    return redirect(url_for('user.bookings'))




#! My Bookings

#View All Own Bookings
@user.route('/bookings')
@user_required
def bookings():
    q = request.args.get('q', '').strip()

    base_query = db.select(Booking).join(Trek, Booking.trek_id == Trek.id).where(Booking.user_id == current_user.id).order_by(Booking.booked_at.desc())
        #* Joined with Trek for search across Trek name — Only for current user !

    if q:
        filters = [Trek.name.ilike(f'%{q}%'), Booking.status.ilike(f'%{q}%'), Booking.payment_status.ilike(f'%{q}%')]
            #Search by trek name, booking status, or payment status
        if q.isdigit():
            filters.append(Booking.id == int(q))
        base_query = base_query.where(or_(*filters))

    booking_list = db.session.execute(base_query).scalars().all()
    return render_template('user/bookings.html', booking_list = booking_list, q = q)



#Cancel Own Booking
@user.route('/bookings/<int:booking_id>/cancel', methods = ['POST'])
@user_required
def cancel_booking(booking_id):
    booking = db.session.get(Booking, booking_id)

    if not booking or booking.user_id != current_user.id:
        flash('Booking not found !', 'danger')
            #* Ownership check — users can only cancel their own bookings
        return redirect(url_for('user.bookings'))

    trek = db.session.get(Trek, booking.trek_id)

    if trek.status in ('Ongoing', 'Completed', 'Cancelled'):
        flash('Booking cannot be cancelled once the trek is ongoing, completed, or cancelled !', 'danger')
        return redirect(url_for('user.bookings'))

    if booking.status == 'Cancelled':
        flash('This booking is already cancelled !', 'warning')
        return redirect(url_for('user.bookings'))

    try:
        booking.status = 'Cancelled'
        trek.available_slots = min(trek.available_slots + 1, trek.total_slots)
            #* Restore slot — capped at total_slots !
            #* Payment Status intentionally left untouched because Staff Manages all the Payments!

        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('Failed to cancel booking. Please try again !', 'danger')
        return redirect(url_for('user.bookings'))

    flash('Booking cancelled successfully. Slot restored !', 'success')
    return redirect(url_for('user.bookings'))




#! User Profile

#Update Profile Info & Update Password
@user.route('/profile', methods = ['GET', 'POST'])
@user_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_no = request.form.get('contact_no', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([name, contact_no]):
            flash('Name and contact number are required !', 'danger')
            return render_template('user/profile.html')

        if not contact_no.isdigit() or len(contact_no) != 10:
            flash('Contact number must be exactly 10 digits !', 'danger')
            return render_template('user/profile.html')

        change_password = any([current_password, new_password, confirm_password])
            #* Password Change is Optional

        if change_password:
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect !', 'danger')
                return render_template('user/profile.html')

            if new_password != confirm_password:
                flash('New passwords do not match !', 'danger')
                return render_template('user/profile.html')

            if len(new_password) < 8:
                flash('New password must be at least 8 characters !', 'danger')
                return render_template('user/profile.html')

        try:
            current_user.name = name
            current_user.contact_no = contact_no

            if change_password:
                current_user.password_hash = generate_password_hash(new_password)

            db.session.commit()

        except Exception:
            db.session.rollback()
            flash('Failed to update profile. Please try again !', 'danger')
            return render_template('user/profile.html')

        flash('Profile updated successfully !', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html')