from main import db
from main.models.base import TimestampMixin
from main.models.video import Video


class Room(db.Model, TimestampMixin):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    current_video = db.Column(db.Integer, db.ForeignKey(Video.id), nullable=True)
    video_time = db.Column(db.Float, nullable=True)
    fingerprint = db.Column(db.String(50))
    status = db.Column(db.String(50))

    def __init__(self, *args, **kwargs):
        super(Room, self).__init__(*args, **kwargs)
