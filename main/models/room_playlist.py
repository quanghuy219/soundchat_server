from main import db
from main.models.base import TimestampMixin


class Media(db.Model, TimestampMixin):
    __tablename__ = 'room_playlist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    status = db.Column(db.String(50))
