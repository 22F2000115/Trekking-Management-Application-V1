from app import app
from database import db
from models import User, StaffProfile, Trek, Booking

with app.app_context():
    db.session.execute(db.delete(Booking))
    db.session.execute(db.delete(Trek))
    db.session.execute(db.delete(StaffProfile))
    non_admins = User.query.filter(User.role != 'Admin').all()
    for u in non_admins:
        db.session.delete(u)
    db.session.commit()
    print("All data cleared. Admin account preserved.")
