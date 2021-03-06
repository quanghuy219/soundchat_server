from flask import request, jsonify

from main import app, db
from main.models.room import Room
from main.models.room_participant import RoomParticipant
from main.models.user import User
from main.utils.helpers import access_token_required
from main.libs.pusher import authenticate, read_pusher_webhook, parse_channel_name, trigger
from main.errors import Error
from main.enums import VideoStatus, ParticipantStatus, PusherEvent


@app.route('/api/pusher/auth', methods=['POST'])
@access_token_required
def authenticate_user(user):
    res = authenticate(request, user)
    if not res:
        raise Error(status_code=400, message='Bad Request')

    return jsonify(res)


@app.route('/api/pusher/webhook', methods=['POST'])
def pusher_webhook():
    webhook = read_pusher_webhook(request)
    events = webhook['events']
    for event in events:
        if event['name'] == 'channel_vacated':
            _handle_channel_vacated(event)
        elif event['name'] == 'member_removed':
            _handle_member_removed(event)
        elif event['name'] == 'member_added':
            _handle_member_added(event)
    return 'ok'


def _handle_channel_vacated(data):
    """When there is no subscribers"""
    channel_name = data['channel']
    room_id = parse_channel_name(channel_name)
    room = Room.query.filter(Room.id == room_id).one()
    if room.status == VideoStatus.PLAYING:
        room.status = VideoStatus.PAUSING
        db.session.commit()


def _handle_member_removed(data):
    channel_name = data['channel']
    room_id = parse_channel_name(channel_name)
    user_id = data['user_id']
    participant = RoomParticipant.query \
        .join(User, User.id == RoomParticipant.user_id) \
        .filter(RoomParticipant.user_id == user_id) \
        .filter(RoomParticipant.room_id == room_id) \
        .one_or_none()

    if participant and participant.status != ParticipantStatus.DELETED:
        data = {
            'user_id': participant.user.id,
            'name': participant.user.name,
            'email': participant.user.email
        }
        trigger(room_id, PusherEvent.EXIT_PARTICIPANT, data)
        participant.status = ParticipantStatus.OUT
        db.session.commit()


def _handle_member_added(data):
    channel_name = data['channel']
    room_id = parse_channel_name(channel_name)
    user_id = data['user_id']

    participant = RoomParticipant.query \
        .join(User, User.id == RoomParticipant.user_id) \
        .filter(RoomParticipant.user_id == user_id) \
        .filter(RoomParticipant.room_id == room_id) \
        .one_or_none()

    if participant and participant.status != ParticipantStatus.DELETED:
        data = {
            'user_id': participant.user.id,
            'name': participant.user.name,
            'email': participant.user.email
        }
        trigger(room_id, PusherEvent.NEW_PARTICIPANT, data)
        participant.status = ParticipantStatus.IN
        db.session.commit()
