from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Function to create the database and tables
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

# Function to add a new user to the database
def add_user(email, username, password):
    # Use the default hashing method (pbkdf2:sha256)
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

# Function to get a user by email (used for login)
def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

# Function to check if the password matches
def check_user_password(user, password):
    return check_password_hash(user.password, password)