from main import db
from main.models.base import TimestampMixin
from main.utils.password import generate_salt, generate_hash


class User(db.Model, TimestampMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(64), nullable=False)
    password_salt = db.Column(db.String(16))
    online = db.Column(db.Integer)
    status = db.Column(db.String(50))

    def __init__(self, *args, **kwargs):
        password = kwargs.pop('password', None)
        if password is not None:
            kwargs['password_salt'] = generate_salt()
            kwargs['password_hash'] = generate_hash(password, kwargs['password_salt'])

        super(User, self).__init__(*args, **kwargs)

    @staticmethod
    def get_user_by_email(email):
        return db.session.query(User).filter_by(email=email).first()
