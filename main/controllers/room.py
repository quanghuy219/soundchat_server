import datetime

from flask import jsonify
from sqlalchemy import desc
from marshmallow import Schema, fields, validate

from main import db, app 
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room import Room
from main.models.room_paticipant import RoomParticipant
from main.models.user import User
from main.models.message import Message
from main.models.room_playlist import RoomPlaylist
from main.models.media import Media
from main.schemas.media import MediaSchema
from main.schemas.room import RoomSchema
from main.schemas.message import MessageSchema
from main.schemas.room_playlist import RoomPlaylistSchema
from main.enums import RoomParticipantStatus, PusherEvent, MediaStatus
from main.schemas.room_participant import RoomParticipantSchema
from main.libs import pusher


@app.route('/api/rooms', methods=['GET'])
@access_token_required
def get_room_list(**kwargs):
    user = kwargs['user']
    all_rooms = db.session.query(Room).all()
    if user is not None: 
        room_list = []
        for room in all_rooms:
            room_participants = db.session.query(RoomParticipant).filter_by(room_id=room.id).all()
            for participant in room_participants:
                if participant.user_id == user.id:
                    room_list.append(RoomSchema().dump(room).data)
        return jsonify({
            'message': "List of user's rooms",
            'data': room_list
        }), 200
    
    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')


@app.route('/api/rooms/<int:room_id>', methods=['GET'])
@access_token_required
def get_room_info(room_id, **kwargs):
    user = kwargs['user']
    room = db.session.query(Room).filter_by(id=room_id).first() 
    if user is not None and room is not None:
        participants = db.session.query(RoomParticipant).filter_by(room_id=room_id).all()
        messages = db.session.query(Message).filter_by(room_id=room_id).all()
        playlist = db.session.query(RoomPlaylist).filter_by(room_id=room_id).all()
        return jsonify({
            'message': 'Room Information',
            'participants': RoomParticipantSchema().dump(participants, many=True).data,
            'messages': MessageSchema().dump(messages, many=True).data,
            'playlist': RoomPlaylistSchema().dump(playlist, many=True).data
        }), 200
    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')


@app.route('/api/rooms', methods=['POST'])
@parse_request_args(RoomSchema())
@access_token_required
def create_room(**kwargs):
    args = kwargs['args']
    user = kwargs['user']
    if User.get_user_by_email(user.email) is not None:
        if db.session.query(Room).filter_by(id=args['id']).first() is None:
            new_room = Room(**args, creator_id=user.id)
            db.session.add(new_room)

            # when creator creates the room, he automatically joins that room 
            creator_participant = RoomParticipant(user_id=user.id, room_id=new_room.id,
                                                  status=RoomParticipantStatus.ACTIVE)
            db.session.add(creator_participant)
            db.session.commit()
            
            return jsonify({
                'message': 'New room is created',
                'data': RoomSchema().dump(new_room).data
            }), 200
        return jsonify({
            'message': 'Room ID existed'
        })
    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')
    

@app.route('/api/rooms/<int:room_id>/users', methods=['POST'])
@access_token_required
def add_participant_to_room(room_id, **kwargs):
    user = kwargs['user']
    room_name = 'presence-room-' + str(room_id)
    room = db.session.query(Room).filter_by(id=room_id).first()
    if User.get_user_by_email(user.email) is not None and room is not None:
        checked_participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
        if checked_participant is None:
            new_participant = RoomParticipant(user_id=user.id, room_id=room_id, status=RoomParticipantStatus.ACTIVE)
            db.session.add(new_participant)
            db.session.commit()

            notification = {
                "name": user.name,
                "user_id": user.id,
                "room": room_id
            }

            pusher.trigger(room_name, PusherEvent.NEW_PARTICIPANT, notification)

            return jsonify({
                'message': 'New participant to the room is created',
                'data': RoomParticipantSchema().dump(new_participant).data
            }), 200
        if checked_participant.status == RoomParticipantStatus.DELETED:
            checked_participant.status = RoomParticipantStatus.ACTIVE
            db.session.commit()

            notification = {
                "name": user.name,
                "user_id": user.id,
                "room": room_id
            }

            pusher.trigger(room_name, PusherEvent.NEW_PARTICIPANT, notification)

            return jsonify({
                'message': 'Participant is re-added to the room',
                'data': RoomParticipantSchema().dump(checked_participant).data
            }), 200
        return jsonify({
            'message': 'Already participated'
        }), StatusCode.FORBIDDEN
    raise Error(StatusCode.UNAUTHORIZED, 'User or room information is invalid')


@app.route('/api/rooms/<int:room_id>/users', methods=['DELETE'])
@access_token_required
def delete_participant_in_room(room_id, **kwargs):
    user = kwargs['user']
    room = db.session.query(Room).filter_by(id=room_id).first()
    if User.get_user_by_email(user.email) is not None and room is not None:
        deleted_participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
        if deleted_participant.status == RoomParticipantStatus.ACTIVE: 
            deleted_participant.status = RoomParticipantStatus.DELETED
            db.session.commit()

            room_name = 'presence-room-' + str(room_id)

            notification = {
                "name": user.name,
                "user_id": user.id,
                "room": room_id
            }

            pusher.trigger(room_name, PusherEvent.DELETE_PARTICIPANT, notification)

            return jsonify({
                'message': 'Participant deleted successfully'
            }), 200 
        return jsonify({
            'message': 'Failed to delete participant'
        }), StatusCode.BAD_REQUEST
    raise Error(StatusCode.UNAUTHORIZED, 'User or room information is invalid')


class SongSchema(Schema):
    type = fields.String(required=True, validate=validate.OneOf(['next', 'current']))


@app.route('/api/room/<int:room_id>/media', methods=['GET'])
@access_token_required
@parse_request_args(SongSchema())
def get_song(room_id, user, args):
    type = args['type']

    room_participant = RoomParticipant.query \
        .filter(RoomParticipant.room_id == room_id) \
        .filter(RoomParticipant.user_id == user.id) \
        .one_or_none()

    if not room_participant:
        raise Error(StatusCode.FORBIDDEN, message='You are not a member of this room')

    if type == 'next':
        song = get_next_media(room_id)
        res = {
            'message': 'Get next song successfully',
            'data': MediaSchema().dumps(song).data
        }
        if song is None:
            res['message'] = 'There is no available next song'

    elif type == 'current':
        song = get_current_media(room_id)
        res = {
            'message': 'Get current song successfully',
            'data': MediaSchema().dumps(song).data
        }
        if song is None:
            res['message'] = 'There is no available song'

    return jsonify(res)


def get_next_media(room_id):
    next_song = Media.query \
        .filter(Media.room_id == room_id) \
        .filter(Media.status == MediaStatus.VOTING) \
        .order_by(desc(Media.total_vote)) \
        .first()

    return next_song


def get_current_media(room_id):
    # Calculate time difference since last update
    room = Room.query.filter(Room.id == room_id).one_or_none()
    if room.current_media is None:
        return None

    if room.status == MediaStatus.PAUSING:
        current_media_time = room.media_time
    else:
        time_diff = (datetime.datetime.utcnow() - room.updated).total_seconds()
        current_media_time = room.media_time + time_diff

    current_song = Media.query.filter(Media.id == room.current_media).one_or_none()
    setattr(current_song, 'media_time', current_media_time)
    return current_song


class MediaStatusUpdateSchema(Schema):
    media_id = fields.Integer(required=True)
    status = fields.String(required=True, validate=validate.OneOf([MediaStatus.READY, MediaStatus.SEEKING,
                                                                  MediaStatus.PAUSING, MediaStatus.PLAYING,
                                                                  MediaStatus.FINISHED]))
    media_time = fields.Float(required=True)


@app.route('/api/rooms/<int:room_id>/media', methods=['PUT'])
@access_token_required
@parse_request_args(MediaStatusUpdateSchema())
def update_media_status(room_id, user, args):
    status = args['status']

    room = Room.query.filter(Room.id == room_id).one()

    if status == MediaStatus.READY:
        # Only play video when all members are ready
        room_member = RoomParticipant.query.filter(RoomParticipant.room_id == room_id) \
                                            .filter(RoomParticipant.user_id == user.id) \
                                            .one()
        room_member.status = MediaStatus.READY
        res = {
            'message': 'Waiting for other members to be ready',
        }
        if _check_all_user_have_same_status(room_id, MediaStatus.READY):
            current_song = get_current_media(room_id)
            pusher.trigger(room_id, PusherEvent.PLAY, MediaSchema().dump(current_song).data)
            room.status = MediaStatus.PLAYING

    if status == MediaStatus.PLAYING:
        # Force all members to play video
        room.media_time = args['media_time']
        room.status = status
        _set_status_for_all_online_user(room_id, MediaStatus.PLAYING)
        pusher.trigger(room_id, PusherEvent.PLAY)
        res = {
            'message': 'Play video'
        }
    if status == MediaStatus.PAUSING:
        # Force all members to pause
        room.media_time = args['media_time']
        room.status = status
        _set_status_for_all_online_user(room_id, MediaStatus.PAUSING)
        pusher.trigger(room_id, PusherEvent.PAUSE)
        res = {
            'message': 'Pause video'
        }
    if status == MediaStatus.SEEKING:
        # If someone seek videos, pause video at that time, and wait for all members to be ready
        room.media_time = args['media_time']
        room.status = MediaStatus.PAUSING
        _set_status_for_all_online_user(room_id, MediaStatus.PAUSING)
        pusher.trigger(room_id, PusherEvent.SEEK, {'media_time': args['media_time']})
        res = {
            'message': 'Seek video'
        }
    if status == MediaStatus.FINISHED:
        room.media_time = args['media_time']
        # If all members are finished their current video, then choose next song to play
        if _check_all_user_have_same_status(room_id, MediaStatus.FINISHED):
            current_song = Media.query.filter(Media.id == room.current_media).one()
            current_song.status = MediaStatus.FINISHED

            next_media = get_next_media(room_id)
            room.status = MediaStatus.PAUSING
            if next_media:
                room.current_media = next_media.id
                room.media_time = 0
                pusher.trigger(room_id, PusherEvent.PROCEED, MediaSchema().dump(next_media).data)
            else:
                room.current_media = None
                room.media_time = 0
        res = {
            'message': 'Wait for other member to finish their video'
        }

    db.session.commit()
    return jsonify(res)


def _check_all_user_have_same_status(room_id, status):
    not_ready_users = RoomParticipant.query.join(User, User.id == RoomParticipant.user_id) \
                        .filter(RoomParticipant.room_id == room_id) \
                        .filter(User.online == 1) \
                        .filter(User.current_room == room_id) \
                        .filter(RoomParticipant.status != status) \
                        .all()

    if not len(not_ready_users):
        return True

    return False


def _set_status_for_all_online_user(room_id, status):
    online_users = RoomParticipant.query.join(User, User.id == RoomParticipant.user_id) \
                        .filter(RoomParticipant.room_id == room_id) \
                        .filter(User.online == 1) \
                        .filter(User.current_room == room_id) \
                        .filter(RoomParticipant.status != status) \
                        .all()

    for user in online_users:
        user.status = status

    db.session.commit()
