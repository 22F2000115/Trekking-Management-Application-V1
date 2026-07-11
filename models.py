from database import db
from flask_login import UserMixin
    #! we use UserMixin from flask_login to add default implementations for user authentication methods:  is_authenticated is_active, is_anonymous, get_id().
    
from datetime import datetime, timezone
    #* We import 'datetime' and 'timezone' for using date and time in our models, especially for preserving Booking and Trekking History !
    
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True) # As this is 'primary_key', by default in 'autoincrement = True'.
    name = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(150), unique = True, nullable = False)
    password_hash = db.Column(db.String(256), nullable = False)
    contact_no = db.Column(db.String(10), nullable = False)
    role = db.Column(db.String(20), nullable = False, default = 'User')
    status = db.Column(db.String(20), nullable = False, default = 'Active')
    created_at = db.Column(db.DateTime(), default = lambda: datetime.now(timezone.utc))
    
    staff_profile = db.relationship('StaffProfile', backref = 'user', uselist = False, cascade = 'all, delete-orphan')
        # one <==> one .
    bookings = db.relationship('Booking', backref = 'user')
        # one <==> many .
    assigned_treks = db.relationship('Trek', backref = 'assigned_staff', foreign_keys = 'Trek.assigned_staff_id')
        # one <==> many relationship between User and Trek, where a staff member can be assigned to multiple treks.
        
    
class StaffProfile(db.Model):
    __tablename__ = 'staff_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    bio = db.Column(db.Text)
    approval_status = db.Column(db.String(20), nullable = False, default = 'Pending')
    
    
    
     
class Trek(db.Model):
    __tablename__ = 'treks'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(150), nullable = False)
    location = db.Column(db.String(150), nullable = False)
    difficulty = db.Column(db.String(20), nullable = False)
    duration = db.Column(db.Integer, nullable = False)          #* Duration in days
    price = db.Column(db.Numeric(10, 2), nullable = False)
    total_slots = db.Column(db.Integer, nullable = False)
    available_slots = db.Column(db.Integer, nullable = False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = True)
    status = db.Column(db.String(20), nullable = False, default = 'Pending')
    start_date = db.Column(db.Date, nullable = False)
    end_date = db.Column(db.Date, nullable = False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(), default = lambda: datetime.now(timezone.utc))
    
    bookings = db.relationship('Booking', backref = 'trek')
        # one <==> many .
    
    
    
class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable = False)
    payment_status = db.Column(db.String(20), nullable = False, default = 'Pending')
    status = db.Column(db.String(20), nullable = False, default = 'Booked')
    booked_at = db.Column(db.DateTime(), default = lambda: datetime.now(timezone.utc))