from main import db
from main.models.base import TimestampMixin


class Media(db.Model, TimestampMixin):
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    url = db.Column(db.Text)
    total_vote = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50))

    def __init__(self, *args, **kwargs):
        super(Media, self).__init__(*args, **kwargs)