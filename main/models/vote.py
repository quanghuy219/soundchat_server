from main import db
from main.models.base import TimestampMixin

class Vote(db.Model, TimestampMixin):
    __tablename__ = 'vote'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship(
        'Media',  
        backref=db.backref('votes',
                        uselist=True,
                        cascade='delete,all'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(
        'User',
        backref=db.backref('votes', 
                        uselist=True,
                        cascade='delete,all'))
    status = db.Column(db.String(50))
