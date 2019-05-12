from flask import jsonify
from marshmallow import Schema, fields, validate

from main import db, app 
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required, create_fingerprint
from main.models.room import Room
from main.models.room_participant import RoomParticipant
from main.models.message import Message
from main.models.room_playlist import RoomPlaylist
from main.models.video import Video
from main.models.vote import Vote
from main.models.user import User
from main.schemas.video import VideoSchema
from main.schemas.room import RoomSchema
from main.schemas.message import MessageSchema
from main.schemas.room_playlist import RoomPlaylistSchema
from main.enums import ParticipantStatus, PusherEvent, VideoStatus, RoomStatus, VoteStatus
from main.schemas.room_participant import RoomParticipantSchema
from main.libs import pusher, video_engine


@app.route('/api/rooms', methods=['GET'])
@access_token_required
def get_room_list(**kwargs):
    user = kwargs['user']
    user_rooms = db.session.query(Room).join(RoomParticipant).filter_by(user_id=user.id).all()
    return jsonify({
        'message': "List of user's rooms",
        'data': RoomSchema(many=True).dump(user_rooms).data
    }), 200


@app.route('/api/rooms/<int:room_id>', methods=['GET'])
@access_token_required
def get_room_info(user, room_id, **kwargs):
    room = db.session.query(Room).filter_by(id=room_id).one_or_none()
    if room is None:
        raise Error(StatusCode.BAD_REQUEST, 'Invalid room id')

    participant = RoomParticipant.query.filter_by(room_id=room_id, user_id=user.id).one_or_none()

    if not participant or participant.status == ParticipantStatus.DELETED:
        raise Error(StatusCode.FORBIDDEN, 'You are not allowed to access room information')

    # Return list of online user
    participants = db.session.query(RoomParticipant).filter_by(room_id=room_id, status=ParticipantStatus.IN).all()
    messages = db.session.query(Message).filter_by(room_id=room_id).all()
    playlist = db.session.query(RoomPlaylist).filter_by(room_id=room_id).all()
    videos = db.session.query(Video).filter_by(room_id=room_id).filter_by(status=VideoStatus.VOTING).all()

    for video in videos:
        user_vote = Vote.query \
            .filter_by(video_id=video.id, user_id=user.id, status=VoteStatus.UPVOTE).one_or_none()
        # Check if user has voted for available video
        if user_vote:
            setattr(video, 'is_voted', True)
        else:
            setattr(video, 'is_voted', False)

    return jsonify({
        'message': 'Room Information',
        'data': {
            'fingerprint': room.fingerprint,
            'name': room.name,
            'participants': RoomParticipantSchema(many=True).dump(participants).data,
            'messages': MessageSchema(many=True).dump(messages).data,
            'playlist': RoomPlaylistSchema(many=True).dump(playlist).data,
            'videos': VideoSchema(many=True).dump(videos).data
        }
    }), 200


@app.route('/api/rooms', methods=['POST'])
@parse_request_args(RoomSchema())
@access_token_required
def create_room(user, **kwargs):
    args = kwargs['args']
    name = args['name']
    room_fingerprint = create_fingerprint()
    new_room = Room(name=name, creator_id=user.id, fingerprint=room_fingerprint, status=RoomStatus.ACTIVE)
    db.session.add(new_room)
    db.session.commit()
    # When creator creates the room, he automatically joins that room
    creator_participant = RoomParticipant(user_id=user.id, room_id=new_room.id, status=ParticipantStatus.IN)
    db.session.add(creator_participant)
    db.session.commit()

    return jsonify({
        'message': 'New room is created',
        'data': RoomSchema().dump(new_room).data
    }), 200


class RoomFingerprint(Schema):
    fingerprint = fields.String(required=True)


@app.route('/api/rooms/fingerprint', methods=['POST'])
@parse_request_args(RoomFingerprint())
@access_token_required
def join_room_by_fingerprint(user, args):
    fingerprint = args['fingerprint']
    room = Room.query.filter(Room.fingerprint == fingerprint).one_or_none()
    if room is None:
        raise Error(StatusCode.BAD_REQUEST, 'Invalid room fingerprint')
    if room.status == RoomStatus.DELETED:
        raise Error(StatusCode.FORBIDDEN, 'This room no longer exists')

    participant = RoomParticipant.query.filter_by(user_id=user.id, room_id=room.id).one_or_none()
    if participant is None:
        participant = RoomParticipant(user_id=user.id, room_id=room.id, status=ParticipantStatus.IN)
        db.session.add(participant)
    else:
        participant.status = ParticipantStatus.IN

    db.session.commit()
    return jsonify({
        'message': 'You have joined this room',
        'data': RoomSchema().dump(room).data
    })


class NewParticipantSchema(Schema):
    email = fields.String(required=True)


@app.route('/api/rooms/<int:room_id>/users', methods=['POST'])
@parse_request_args(NewParticipantSchema())
@access_token_required
def add_participant_to_room(room_id, user, args):
    room = db.session.query(Room).filter_by(id=room_id).one_or_none()

    if room is None:
        raise Error(StatusCode.BAD_REQUEST, 'Invalid room id')

    # Only room member can add new participant
    checked_participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).one_or_none()
    if checked_participant is None or checked_participant.status == ParticipantStatus.DELETED:
        raise Error(StatusCode.FORBIDDEN, 'You\'re not allowed to add new member to this room')

    added_user = User.query.filter_by(email=args['email']).one_or_none()
    if not added_user:
        raise Error(StatusCode.BAD_REQUEST, 'This user does not exist')

    is_participant = RoomParticipant.query.filter_by(user_id=added_user.id, room_id=room_id).one_or_none()
    if not is_participant:
        new_participant = RoomParticipant(user_id=user.id, room_id=room_id, status=ParticipantStatus.OUT)
        db.session.add(new_participant)
        db.session.commit()

        notification = {
            "name": added_user.name,
            "user_id": added_user.id,
            "room": room_id
        }

        pusher.trigger(room_id, PusherEvent.NEW_PARTICIPANT, notification)

        return jsonify({
            'message': 'New participant to the room is created',
            'data': RoomParticipantSchema().dump(new_participant).data
        }), 200
    elif is_participant.status == ParticipantStatus.OUT or is_participant.status == ParticipantStatus.DELETED:
        # User is re-added to this room
        checked_participant.status = ParticipantStatus.IN
        db.session.commit()

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
    raise Error(StatusCode.UNAUTHORIZED, 'This user is already a member of this room')


@app.route('/api/rooms/<int:room_id>/users', methods=['DELETE'])
@access_token_required
def delete_participant_in_room(room_id, **kwargs):
    user = kwargs['user']
    room = db.session.query(Room).filter_by(id=room_id).first()
    if room is None:
        raise Error(StatusCode.BAD_REQUEST, 'Invalid room id')

    deleted_participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
    if deleted_participant.status == ParticipantStatus.IN:
        deleted_participant.status = ParticipantStatus.DELETED
        db.session.commit()

        notification = {
            "name": user.name,
            "user_id": user.id,
            "room": room_id
        }

        pusher.trigger(room_id, PusherEvent.DELETE_PARTICIPANT, notification)

        return jsonify({
            'message': 'Participant deleted successfully'
        }), 200

    raise Error(StatusCode.UNAUTHORIZED, 'Failed to delete participant')


@app.route('/api/rooms/<int:room_id>/users', methods=['PUT'])
@access_token_required
def participant_exit_room(room_id, **kwargs):
    user = kwargs['user']
    room = db.session.query(Room).filter_by(id=room_id).first()
    if room is None:
        raise Error(StatusCode.BAD_REQUEST, 'Invalid room id')

    participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
    if participant.status == ParticipantStatus.IN:
        participant.status = ParticipantStatus.OUT
        db.session.commit()

        notification = {
            "name": user.name,
            "user_id": user.id,
            "room": room_id
        }

        pusher.trigger(room_id, PusherEvent.EXIT_PARTICIPANT, notification)

        return jsonify({
            'message': 'Participant exited successfully'
        }), 200
    raise Error(StatusCode.UNAUTHORIZED, 'participant failed to exit')


class SongSchema(Schema):
    type = fields.String(required=True, validate=validate.OneOf(['next', 'current']))


@app.route('/api/rooms/<int:room_id>/videos', methods=['GET'])
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
        song = video_engine.get_next_video(room_id)
        res = {
            'message': 'Get next song successfully',
            'data': VideoSchema().dump(song).data
        }
        if song is None:
            res['message'] = 'There is no available next song'

    elif type == 'current':
        song = video_engine.get_current_video(room_id)
        res = {
            'message': 'Get current song successfully',
            'data': VideoSchema().dump(song).data
        }
        if song is None:
            res['message'] = 'There is no available song'

    return jsonify(res)


class MediaStatusUpdateSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf([VideoStatus.READY, VideoStatus.SEEKING,
                                                                   VideoStatus.PAUSING, VideoStatus.PLAYING,
                                                                   VideoStatus.FINISHED]))
    video_time = fields.Float(required=True)


@app.route('/api/rooms/<int:room_id>/videos', methods=['PUT'])
@access_token_required
@parse_request_args(MediaStatusUpdateSchema())
def update_video_status(room_id, user, args):
    status = args['status']

    room = Room.query.filter(Room.id == room_id).one()

    if status == VideoStatus.READY:
        # Only play video when all members are ready
        room_member = RoomParticipant.query.filter(RoomParticipant.room_id == room_id) \
                                            .filter(RoomParticipant.user_id == user.id) \
                                            .one()
        room_member.video_status = VideoStatus.READY
        res = {
            'message': 'Waiting for other members to be ready',
        }
        if video_engine.check_all_user_have_same_video_status(room_id, VideoStatus.READY):
            current_video = video_engine.get_current_video(room_id)
            event_data = {
                'event': VideoStatus.PLAYING,
                'data': VideoSchema().dump(current_video).data
            }
            pusher.trigger(room_id, PusherEvent.MEDIA_STATUS_CHANGED, event_data)
            video_engine.set_online_users_video_status(room_id, VideoStatus.PLAYING)
            room.status = VideoStatus.PLAYING

    if status == VideoStatus.PLAYING:
        # Force all members to play video
        room.video_time = args['video_time']
        room.status = status
        video_engine.set_online_users_video_status(room_id, VideoStatus.PLAYING)
        current_song = video_engine.get_current_video(room_id)
        event_data = {
            'event': VideoStatus.PLAYING,
            'data': VideoSchema().dump(current_song).data
        }
        pusher.trigger(room_id, PusherEvent.MEDIA_STATUS_CHANGED, event_data)
        res = {
            'message': 'Play video'
        }
    if status == VideoStatus.PAUSING:
        # Force all members to pause
        room.video_time = args['video_time']
        room.status = status
        video_engine.set_online_users_video_status(room_id, VideoStatus.PAUSING)
        current_song = video_engine.get_current_video(room_id)
        event_data = {
            'event': VideoStatus.PAUSING,
            'data': VideoSchema().dump(current_song).data
        }
        pusher.trigger(room_id, PusherEvent.MEDIA_STATUS_CHANGED, event_data)
        res = {
            'message': 'Pause video'
        }
    if status == VideoStatus.SEEKING:
        # If someone seek videos, pause video at that time, and wait for all members to be ready
        room.video_time = args['video_time']
        room.status = VideoStatus.PAUSING
        video_engine.set_online_users_video_status(room_id, VideoStatus.PAUSING)
        current_song = video_engine.get_current_video(room_id)
        event_data = {
            'event': VideoStatus.SEEKING,
            'data': VideoSchema().dump(current_song).data
        }
        pusher.trigger(room_id, PusherEvent.MEDIA_STATUS_CHANGED, event_data)
        res = {
            'message': 'Seek video'
        }
    if status == VideoStatus.FINISHED:
        room_member = RoomParticipant.query.filter(RoomParticipant.room_id == room_id) \
            .filter(RoomParticipant.user_id == user.id) \
            .one()

        room.video_time = args['video_time']
        room_member.video_status = VideoStatus.FINISHED

        # If all members are finished their current video, then choose next song to play
        if video_engine.check_all_user_have_same_video_status(room_id, VideoStatus.FINISHED):
            current_song = Video.query.filter(Video.id == room.current_video).one()
            current_song.status = VideoStatus.FINISHED

            video_engine.set_online_users_video_status(room_id, VideoStatus.PAUSING)
            next_video = video_engine.set_current_video(room_id)
            parsed_next_video = VideoSchema().dump(next_video).data
            if parsed_next_video:
                parsed_next_video['video_time'] = 0
                parsed_next_video['status'] = VideoStatus.PAUSING
            pusher.trigger(room_id, PusherEvent.PROCEED, parsed_next_video)

        res = {
            'message': 'Wait for other member to finish their video'
        }

    db.session.commit()
    return jsonify(res)
