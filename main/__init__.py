import logging

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_cors import CORS
from redis import Redis
import pusher

from main.cfg import config
from main.errors import Error

app = Flask(__name__)
app.config.from_object(config)

_naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

_metadata = MetaData(naming_convention=_naming_convention)
db = SQLAlchemy(app=app, metadata=_metadata)

CORS(app)
redis = Redis.from_url(config.REDIS_URI)

pusher_client = pusher.Pusher(
  app_id=config.PUSHER_APP_ID,
  key=config.PUSHER_KEY,
  secret=config.PUSHER_SECRET,
  cluster=config.PUSHER_CLUSTER
)


def _register_subpackages():
    import main.errors
    import main.controllers


_register_subpackages()


@app.errorhandler(404)
def handle_not_found(exception):
    """Handle an invalid endpoint"""
    return jsonify({
        'message': 'Resource not found'
    }), 404


@app.errorhandler(Error)
def handle_exception(error):
    return error.to_response()


@app.errorhandler(500)
def handle_internal_error(exception):
    """Rollback database transaction if any error occurs"""
    logging.error(exception)
    db.session.rollback()
    return jsonify({
        'message': 'An unexpected internal error has occurred'
    }), 500
