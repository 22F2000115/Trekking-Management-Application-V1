from flask import Flask, render_template
from database import db
from flask_login import LoginManager
    #! Handles user sessions
from models import User
from werkzeug.security import generate_password_hash
    #! Hashes passwords

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.debug = True
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.sqlite3'
        # SQLite DB file
    app.config['SECRET_KEY'] = 'trekking_app_secret_key'
        # Signs session cookies
        
    login_manager.init_app(app)
        # Bind LoginManager to app
    login_manager.login_view = 'auth.login'
        # Redirect unauthenticated users
    db.init_app(app)
        # Bind SQLAlchemy to app
        
    #* Imported here to avoid circular imports
    from controllers.admin import admin
    from controllers.auth import auth
    from controllers.main import main
    from controllers.staff import staff
    from controllers.user import user
    
    app.register_blueprint(auth)      #Authentication Blueprint
    app.register_blueprint(main)      #Main Blueprint
    app.register_blueprint(admin)     #Admin Blueprint
    app.register_blueprint(staff)     #Staff Blueprint
    app.register_blueprint(user)      #User Blueprint

    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
        #Loads user by ID for Flask-Login


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403
        #Custom 403 Error Handler, Renders 403.html


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
            #* Create all the tables from models
        
        admin_user = db.session.execute(db.select(User).filter_by(role = 'Admin')).scalar_one_or_none()
        if admin_user is None:
            admin_user = User(name = 'Trekk App Admin', email = 'admin@trekkapp.com', password_hash = generate_password_hash('Admin@123'), contact_no = '9876543210', role = 'Admin', status = 'Active')
            db.session.add(admin_user)
            db.session.commit()
            print("'Admin Created Successfully' with the credentials we provided earlier.")
        
    app.run()