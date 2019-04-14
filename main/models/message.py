from main import db
from main.models.base import TimestampMixin

class Message(db.Model, TimestampMixin):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(
        'User',
        backref=db.backref('messages',
                        uselist=True))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    room = db.relationship(
        'Room',
        backref=db.backref('messages',
                        uselist=True,
                        cascade='delete,all'))
    room = db.relationship('Room')
    content = db.Column(db.Text)
    status = db.Column(db.String(50))
