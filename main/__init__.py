import logging

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

from main.cfg import config
from main.error import Error

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)


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
