import datetime
from functools import wraps
import logging

import jwt
from flask import request

from main import db
from main.cfg import config
from main.error import Error, StatusCode
from main.models.user import UserModel


def encode(account):
    iat = datetime.datetime.utcnow()
    return jwt.encode({
        'sub': account.id,
        'account_type': account.account_type,
        'iat': iat,
        'exp': iat + datetime.timedelta(days=365)
    }, config.SECRET_KEY).decode('utf-8')


def decode(access_token):
    try:
        token = jwt.decode(access_token, config.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        # Check that token is expired
        errors = {
            "token": "Token has expired. Please login again"
        }
        raise Error(StatusCode.UNAUTHORIZED, "Your session has expired. Please login again", errors)
    except jwt.InvalidTokenError as e:
        # Check that token is invalid
        logging.error(e)
        errors = {
            "token": "Invalid token"
        }
        raise Error(StatusCode.UNAUTHORIZED, "Request unauthorized", errors)

    return token


def parse_request_args(schema):
    def parse_request_args_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            request_args = request.get_json() or {}
            if request.method == 'GET':
                request_args = request.args.to_dict()
            parsed_args, errors = schema.load(request_args)
            if errors:
                raise Error(StatusCode.BAD_REQUEST, 'Bad request', errors)
            kwargs['args'] = parsed_args
            return f(*args, **kwargs)

        return decorated_function

    return parse_request_args_decorator


def access_token_require(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authorization = None
        if 'Authorization' in request.headers:
            authorization = request.headers['Authorization']

        if not authorization or not authorization.startswith('Bearer '):
            errors = {
                'token': 'Invalid authorization header'
            }
            logging.error('Invalid authorization header')
            raise Error(StatusCode.BAD_REQUEST, 'Bad request', errors)

        # Decode the token which has been passed in the request headers
        token = decode(authorization[len('Bearer '):])

        account = db.session.query(UserModel).filter_by(id=token['sub']).one_or_none()

        if not account:
            raise Error(StatusCode.UNAUTHORIZED, 'Unauthorized')

        kwargs['user'] = account
        return f(*args, **kwargs)

    return decorated_function
