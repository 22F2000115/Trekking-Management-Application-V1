from flask import Flask
app = None
from database import db
    #!We import 'db' from '~/database.py' to initialize it with our Flask app later on.
from models import *
from werkzeug.security import generate_password_hash
    #! We import 'generate_password_hash' from 'werkzeug.security' to hash the admin password before storing it in the database for better security.

def create_app():
    app = Flask(__name__)
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.sqlite3'
    
        #* This is the Database URI for the SQLite database. 'sqlite:///' prefix indicates that we are using SQLite for our Database, and 'trekking.sqlite3' is the name of the Database File. If the File doesn't exist it will be created automatically when we run the application.
        
    db.init_app(app)
    
        #* This line initializes the SQLAlchemy instance 'db' with our Flask app. So that we can use SQLAlchemy's features to interact with our database in the application.
    app.app_context().push()
    
        #* This line pushes the application context. This is necessary because some operations (like database interactions) require an application context to be active.
    
    return app

app = create_app()
    #* This creates our app with all the configurations we provided in the 'create_app' function.





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
            #! This creates all the tables in the database based on the models defined in 'models.py'.
        
        Admin = User.query.filter_by(role = 'Admin').first()
        if Admin is None:
            Admin = User(name = 'Admin_Trekk_App', email = 'admin@trekkapp.com', password_hash = generate_password_hash('Admin@123'), role = 'Admin', status = 'Active')
            db.session.add(Admin)
            db.session.commit()
            print("'Admin Created Successfully' with the credentials we provided earlier.")
        
    app.run()