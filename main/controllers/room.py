from flask import jsonify
from marshmallow import Schema, fields, validate

from main import db, app 
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room import Room
from main.models.room_paticipant import RoomParticipant
from main.models.message import Message
from main.models.room_playlist import RoomPlaylist
from main.models.media import Media
from main.schemas.media import MediaSchema
from main.schemas.room import RoomSchema
from main.schemas.message import MessageSchema
from main.schemas.room_playlist import RoomPlaylistSchema
from main.enums import ParticipantStatus, PusherEvent, MediaStatus, RoomStatus
from main.schemas.room_participant import RoomParticipantSchema
from main.libs import pusher
from main.libs import media_engine


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
@access_token_required
def create_room(user):
    new_room = Room(creator_id=user.id, status=RoomStatus.ACTIVE)
    db.session.add(new_room)

    # When creator creates the room, he automatically joins that room
    creator_participant = RoomParticipant(user_id=user.id, room_id=new_room.id, status=ParticipantStatus.IN)
    db.session.add(creator_participant)
    db.session.commit()

    return jsonify({
        'message': 'New room is created',
        'data': RoomSchema().dump(new_room).data
    }), 200
    

@app.route('/api/rooms/<int:room_id>/users', methods=['POST'])
@access_token_required
def add_participant_to_room(room_id, **kwargs):
    user = kwargs['user']
    room = db.session.query(Room).filter_by(id=room_id).first()
    if room is not None:
        checked_participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
        if checked_participant is None:
            new_participant = RoomParticipant(user_id=user.id, room_id=room_id, status=ParticipantStatus.IN)
            db.session.add(new_participant)
            db.session.commit()

            notification = {
                "name": user.name,
                "user_id": user.id,
                "room": room_id
            }

            pusher.trigger(room_id, PusherEvent.NEW_PARTICIPANT, notification)

            return jsonify({
                'message': 'New participant to the room is created',
                'data': RoomParticipantSchema().dump(new_participant).data
            }), 200
        if checked_participant.status == ParticipantStatus.OUT or checked_participant.status == ParticipantStatus.DELETED:
            checked_participant.status = ParticipantStatus.IN
            user.current_room = room_id

            notification = {
                "name": user.name,
                "user_id": user.id,
                "room": room_id
            }

            pusher.trigger(room_id, PusherEvent.NEW_PARTICIPANT, notification)

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
    if room is not None:
        deleted_participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
        if deleted_participant.status == ParticipantStatus.IN:
            deleted_participant.status = ParticipantStatus.DELETED
            user.current_room = None
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


@app.route('/api/rooms/<int:room_id>/users', methods=['PUT'])
@access_token_required
def participant_exit_room(room_id, **kwargs):
    user = kwargs['user']
    room = db.session.query(Room).filter_by(id=room_id).first()
    if room is not None:
        participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
        if participant.status == ParticipantStatus.IN:
            participant.status = ParticipantStatus.OUT
            user.current_room = None
            db.session.commit()

            room_name = 'presence-room-' + str(room_id)

            notification = {
                "name": user.name,
                "user_id": user.id,
                "room": room_id
            }

            pusher.trigger(room_name, PusherEvent.EXIT_PARTICIPANT, notification)

            return jsonify({
                'message': 'Participant exited successfully'
            }), 200
        return jsonify({
            'message': 'participant failed to exit'
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
        song = media_engine.get_next_media(room_id)
        res = {
            'message': 'Get next song successfully',
            'data': MediaSchema().dumps(song).data
        }
        if song is None:
            res['message'] = 'There is no available next song'

    elif type == 'current':
        song = media_engine.get_current_media(room_id)
        res = {
            'message': 'Get current song successfully',
            'data': MediaSchema().dumps(song).data
        }
        if song is None:
            res['message'] = 'There is no available song'

    return jsonify(res)


class MediaStatusUpdateSchema(Schema):
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
        room_member.media_status = MediaStatus.READY
        res = {
            'message': 'Waiting for other members to be ready',
        }
        if media_engine.check_all_user_have_same_media_status(room_id, MediaStatus.READY):
            current_song = media_engine.get_current_media(room_id)
            pusher.trigger(room_id, PusherEvent.PLAY, MediaSchema().dump(current_song).data)
            media_engine.set_online_users_media_status(room_id, MediaStatus.PLAYING)
            room.status = MediaStatus.PLAYING

    if status == MediaStatus.PLAYING:
        # Force all members to play video
        room.media_time = args['media_time']
        room.status = status
        media_engine.set_online_users_media_status(room_id, MediaStatus.PLAYING)
        pusher.trigger(room_id, PusherEvent.PLAY)
        res = {
            'message': 'Play video'
        }
    if status == MediaStatus.PAUSING:
        # Force all members to pause
        room.media_time = args['media_time']
        room.status = status
        media_engine.set_online_users_media_status(room_id, MediaStatus.PAUSING)
        pusher.trigger(room_id, PusherEvent.PAUSE)
        res = {
            'message': 'Pause video'
        }
    if status == MediaStatus.SEEKING:
        # If someone seek videos, pause video at that time, and wait for all members to be ready
        room.media_time = args['media_time']
        room.status = MediaStatus.PAUSING
        media_engine.set_online_users_media_status(room_id, MediaStatus.PAUSING)
        pusher.trigger(room_id, PusherEvent.SEEK, {'media_time': args['media_time']})
        res = {
            'message': 'Seek video'
        }
    if status == MediaStatus.FINISHED:
        room_member = RoomParticipant.query.filter(RoomParticipant.room_id == room_id) \
            .filter(RoomParticipant.user_id == user.id) \
            .one()

        room.media_time = args['media_time']
        room_member.media_status = MediaStatus.FINISHED

        # If all members are finished their current video, then choose next song to play
        if media_engine.check_all_user_have_same_media_status(room_id, MediaStatus.FINISHED):
            current_song = Media.query.filter(Media.id == room.current_media).one()
            current_song.status = MediaStatus.FINISHED

            next_media = media_engine.get_next_media(room_id)
            room.status = MediaStatus.PAUSING
            media_engine.set_online_users_media_status(room_id, MediaStatus.PAUSING)
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
