from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db

ROLE_CASHIER = 'cashier'
ROLE_DIRECTOR = 'director'


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_CASHIER)
    full_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    sales = db.relationship('Sale', backref='cashier', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_director(self):
        return self.role == ROLE_DIRECTOR

    def is_cashier(self):
        return self.role == ROLE_CASHIER

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class UserRepo:
    def get_by_username(self, username):
        return User.query.filter_by(username=username).first()

    def get_by_id(self, user_id):
        return User.query.get(user_id)

    def add(self, username, password, role=ROLE_CASHIER, full_name=None):
        user = User(username=username, role=role, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def all(self):
        return User.query.all()

    def update(self, user_id, username=None, password=None, role=None, full_name=None):
        user = self.get_by_id(user_id)
        if not user:
            return None
        if username:
            user.username = username
        if password:
            user.set_password(password)
        if role:
            user.role = role
        if full_name is not None:
            user.full_name = full_name
        db.session.commit()
        return user

    def delete(self, user_id):
        user = self.get_by_id(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False

    def filter_by_role(self, role):
        return User.query.filter_by(role=role).all()