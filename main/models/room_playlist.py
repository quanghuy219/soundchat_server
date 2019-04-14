from main import db
from main.models.base import TimestampMixin

class RoomPlaylist(db.Model, TimestampMixin):
    __tablename__ = 'room_playlist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    room = db.relationship(
        'Room',
        backref=db.backref('playlist',
                        uselist=False,
                        cascade='delete,all'))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    status = db.Column(db.String(50))
