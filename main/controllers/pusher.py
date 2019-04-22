from flask import request, jsonify

from main import app, db
from main.models.room import Room
from main.models.room_paticipant import RoomParticipant
from main.utils.helpers import access_token_required
from main.libs.pusher import authenticate, read_pusher_webhook, parse_channel_name
from main.errors import Error
from main.enums import MediaStatus, ParticipantStatus


@app.route('/pusher/auth', methods=['POST'])
@access_token_required
def authenticate_user(user):
    res = authenticate(request, user)
    if not res:
        raise Error(status_code=400, message='Bad Request')

    return jsonify(res)


@app.route('/pusher/webhook', methods=['POST'])
def pusher_webhook():
    webhook = read_pusher_webhook(request)
    events = webhook['events']
    print(webhook)
    for event in events:
        if event['name'] == 'channel_vacated':
            _handle_channel_vacated(event)
        elif event['name'] == 'member_removed':
            _handle_member_removed(event)
    return 'ok'


def _handle_channel_vacated(data):
    """When there is no subscribers"""
    channel_name = data['channel']
    room_id = parse_channel_name(channel_name)
    room = Room.query.filter(Room.id == room_id).one()
    if room.status == MediaStatus.PLAYING:
        room.status = MediaStatus.PAUSING
        db.session.commit()


def _handle_member_removed(data):
    channel_name = data['channel']
    room_id = parse_channel_name(channel_name)
    user_id = data['user_id']

    participant = RoomParticipant.query \
        .filter(RoomParticipant.user_id == user_id) \
        .filter(RoomParticipant.room_id == room_id) \
        .one()

    participant.status = ParticipantStatus.OUT
    db.session.commit()


