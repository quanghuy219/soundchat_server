from main import db
from main.models.base import TimestampMixin


class Vote(db.Model, TimestampMixin):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'))
    video = db.relationship('Video', backref=db.backref('votes', uselist=True, cascade='delete,all'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('votes',  uselist=True, cascade='delete,all'))
    status = db.Column(db.String(50))

    def __init__(self, *args, **kwargs):
        super(Vote, self).__init__(*args, **kwargs)
