from main import db
from main.models.base import TimestampMixin


class Room(db.Model, TimestampMixin):
    __tablename__ = 'room'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    current_media = db.Column(db.Integer, db.ForeignKey('media.id'))
    status = db.Column(db.String(50))
