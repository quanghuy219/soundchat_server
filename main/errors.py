from flask import jsonify


class Error(Exception):
    def __init__(self, status_code, message='', errors=None):
        super(Error)
        self.message = message
        self.error_data = errors or {}
        self.status_code = status_code

    def to_response(self):
        resp = {
            'message': self.message,
            'error_data': self.error_data
        }
        return jsonify(resp), self.status_code


class StatusCode:
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
