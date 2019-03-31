from main import db
from main.models.base import TimestampMixin


class Media(db.Model, TimestampMixin):
    __tablename__ = 'vote'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50))
