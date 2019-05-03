from main import db
from main.models.base import TimestampMixin


class RoomPlaylist(db.Model, TimestampMixin):
    __tablename__ = 'room_playlist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    room = db.relationship('Room', backref=db.backref('playlist', uselist=False, cascade='delete,all'))
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    status = db.Column(db.String(50))

    def __init__(self, *args, **kwargs):
        super(RoomPlaylist, self).__init__(*args, **kwargs)
