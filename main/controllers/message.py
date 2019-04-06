from flask import jsonify

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.user import User
from main.models.room import Room
from main.models.message import Message
from main.schemas.user import UserSchema
from main.schemas.room import RoomSchema
from main.schemas.message import MessageSchema
from main.enums import UserStatus

@app.route('/api/messages', methods=['POST'])
@parse_request_args(MessageSchema())
@access_token_required
def send_message(**kwargs):
    user = kwargs['user']
    args = kwargs['args']

    if User.get_user_by_email(user.email) is not None: 
        message = Message(**args, user_id=user.id)
        db.session.add(message)
        db.session.commit()
        return jsonify({
            'message': 'message added successfully',
            'data': MessageSchema().dump(message).data
        }), 200
    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')
    
