from main import db
from main.models.base import TimestampMixin


class RoomParticipant(db.Model, TimestampMixin):
    __tablename__ = 'room_paticipant'

    id = db.Column(db.Integer, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), primary_key=True)
    room = db.relationship('Room')
    status = db.Column(db.String(50))
