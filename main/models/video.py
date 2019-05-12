from main import db
from main.models.base import TimestampMixin


class Video(db.Model, TimestampMixin):
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator = db.relationship('User')
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    url = db.Column(db.Text)
    total_vote = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50))

    def __init__(self, *args, **kwargs):
        super(Video, self).__init__(*args, **kwargs)
