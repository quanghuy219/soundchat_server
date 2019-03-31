import logging

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_cors import CORS

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


def _register_subpackages():
    import main.errors
    import main.controllers


_register_subpackages()


@app.errorhandler(404)
def handle_not_found(exception):
    """Handle an invalid endpoint"""
    return jsonify({
        'error_message': 'Resource not found'
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
        'error_message': 'An unexpected internal error has occurred'
    }), 500
