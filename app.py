from flask import Flask, render_template
from database import db
    #! Imports the SQLAlchemy instance to be initialized with the app later.
from flask_login import LoginManager
    #! Manages user sessions and authentication.
from models import User
from werkzeug.security import generate_password_hash
    #! Used to hash the password before storing it in the DB.

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.debug = True
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.sqlite3'
        # SQLite DB URI — creates 'trekking.sqlite3' if it doesn't exist.
    app.config['SECRET_KEY'] = 'trekking_app_secret_key'
        # Required for signing session cookies — Flask-Login and flash messages depend on this.
        
    login_manager.init_app(app)
        # Ties LoginManager to the Flask app.
    login_manager.login_view = 'auth.login'
        # Redirects unauthenticated users to the login page.
    db.init_app(app)
        # Ties SQLAlchemy to the Flask app.
        
    #* Blueprints imported and registered inside create_app — to avoid circular imports.
    from controllers.auth import auth
    from controllers.main import main
    
    app.register_blueprint(auth) #Auth Blueprint
    app.register_blueprint(main) #Main Blueprint

    return app

app = create_app()
    # This creates our app with all the configurations we provided in the 'create_app' function.

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
        # Fetches User from DB by ID on every request — makes them available as 'current_user'.


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403
        # Renders '403.html' when a user tries to access an unauthorized route.


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
            #* Creates all DB tables based on 'models.py' .
        
        admin_user = db.session.execute(db.select(User).filter_by(role = 'Admin')).scalar_one_or_none()
        if admin_user is None:
            admin_user = User(name = 'Trekk App Admin', email = 'admin@trekkapp.com', password_hash = generate_password_hash('Admin@123'), contact_no = '9876543210', role = 'Admin', status = 'Active')
            db.session.add(admin_user)
            db.session.commit()
            print("'Admin Created Successfully' with the credentials we provided earlier.")
        
    app.run()