from flask import jsonify

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.user import User
from main.models.room import Room
from main.models.room_paticipant import RoomParticipant
from main.models.message import Message
from main.schemas.message import MessageSchema
from main.enums import PusherEvent
from main.libs import pusher


@app.route('/api/messages', methods=['POST'])
@parse_request_args(MessageSchema())
@access_token_required
def send_message(**kwargs):
    user = kwargs['user']
    args = kwargs['args']

    if User.get_user_by_email(user.email) is not None: 
        message = Message(user_id=user.id, **args)
        room = db.session.query(Room).filter_by(id=args['room_id']).first() # query room to get room's name to use later 
        if room is not None: 
            participant = db.session.query(RoomParticipant).filter_by(room_id=room.id, user_id=user.id).first()
            if participant:
                db.session.add(message)
                db.session.commit()

                data = {
                    "username": participant.name,
                    "room": room.name,
                    "message": args['content']
                }

                pusher.trigger(room.name, PusherEvent.NEW_MESSAGE, data)

                return jsonify({
                    'message': 'message added successfully',
                    'data': MessageSchema().dump(message).data
                }), 200
        return jsonify({
            "message": "invalid room access"
        }), StatusCode.FORBIDDEN
    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')
