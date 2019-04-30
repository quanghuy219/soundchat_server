from flask import jsonify

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room_participant import RoomParticipant
from main.models.message import Message
from main.schemas.message import MessageSchema
from main.libs import pusher
from main.enums import PusherEvent, ParticipantStatus


@app.route('/api/messages', methods=['POST'])
@parse_request_args(MessageSchema())
@access_token_required
def send_message(user, args):
    room_id = args['room_id']

    participant = db.session.query(RoomParticipant).filter_by(room_id=args['room_id'], user_id=user.id).first()
    if participant.status != ParticipantStatus.IN:
        raise Error(StatusCode.FORBIDDEN, message='Invalid room access')

    message = Message(user_id=user.id, **args)
    db.session.add(message)
    db.session.commit()

    data = {
        'user_id': user.id,
        'username': user.name,
        'room_id': room_id,
        'content': args['content']
    }
    pusher.trigger(room_id, PusherEvent.NEW_MESSAGE, data)

    return jsonify({
        'message': 'Message added successfully',
        'data': MessageSchema().dump(message).data
    }), 200
