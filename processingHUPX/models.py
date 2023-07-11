from processingHUPX import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#new class for the User model for storing the users in this way
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    db_name = db.Column(db.String(60), nullable=False, unique=True)
    is_admin = db.Column(db.Integer, default=2) #1 - admin; 2 - user
    requests = db.relationship('Request', backref='owner', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def is_administrator(self):
        return self.is_admin

#new class for the Request model for storing the requests in this way
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_requested = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    img_name = db.Column(db.String(30), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    table_name = db.Column(db.String(60), nullable=False, unique=True)
    boxes = db.Column(db.String(20), nullable=False)
    div_file = db.Column(db.String(60), nullable=False, unique=True)
    js_file = db.Column(db.String(60), nullable=False, unique=True)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
