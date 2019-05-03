from main import db
from main.models.base import TimestampMixin


class Message(db.Model, TimestampMixin):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    room = db.relationship('Room')
    content = db.Column(db.Text(collation='utf8mb4_unicode_ci'))
    status = db.Column(db.String(50))

    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)
