from flask import jsonify

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.user import User
from main.models.room_paticipant import RoomParticipant
from main.models.message import Message
from main.schemas.message import MessageSchema
from main.libs import pusher
from main.enums import PusherEvent, ParticipantStatus


@app.route('/api/messages', methods=['POST'])
@parse_request_args(MessageSchema())
@access_token_required
def send_message(**kwargs):
    user = kwargs['user']
    args = kwargs['args']

    if User.get_user_by_email(user.email) is not None: 
        participant = db.session.query(RoomParticipant).filter_by(room_id=args['room_id'], user_id=user.id).first()
        if participant.status == ParticipantStatus.IN:
            message = Message(user_id=user.id, **args)
            db.session.add(message)
            db.session.commit()
            room_name = 'presence-room-'+str(args['room_id'])
            data = {
                "username": user.name,
                "room": room_name,
                "message": args['content']
            }
            pusher.trigger(room_name, PusherEvent.NEW_MESSAGE, data)

            return jsonify({
                'message': 'message added successfully',
                'data': MessageSchema().dump(message).data
            }), 200

        raise Error(StatusCode.FORBIDDEN, message='invalid room access')

    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')
