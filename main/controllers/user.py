from flask import jsonify

from main import db, app
from main.errors import Error, StatusCode
from main.utils import password as pw
from main.utils.helpers import encode, parse_request_args
from main.models.user import User
from main.schemas.user import UserSchema
from main.enums import UserStatus


@app.route('/api/login', methods=['POST'])
@parse_request_args(UserSchema(exclude=['name']))
def login(args):
    user = db.session.query(User).filter_by(email=args['email']).one_or_none()
    if user is not None and pw.generate_hash(args['password'], user.password_salt) == user.password_hash:
        return jsonify({
            'message': 'Login success',
            'access_token': encode(user),
            'data': UserSchema().dump(user).data
        }), 200

    raise Error(StatusCode.UNAUTHORIZED, 'Email or password is incorrect')


@app.route('/api/users', methods=['POST'])
@parse_request_args(UserSchema())
def register_new_user(**kwargs):
    args = kwargs['args']
    email = args['email']

    if User.get_user_by_email(email) is not None:
        raise Error(StatusCode.BAD_REQUEST, 'This email has been registered before')

    user = User(**args, status=UserStatus.ACTIVE)
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'message': 'New account for student is created',
        'data': UserSchema().dump(user).data
    }), 200
