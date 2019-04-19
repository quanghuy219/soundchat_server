import datetime

from flask import jsonify
from sqlalchemy import func
from marshmallow import Schema, fields, validate, validates_schema

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room import Room
from main.models.room_paticipant import RoomParticipant
from main.models.user import User
from main.models.media import Media
from main.models.vote import Vote
from main.schemas.media import MediaSchema
from main.libs import pusher
from main.enums import MediaStatus, VoteStatus, PusherEvent


class SongSchema(Schema):
    room_id = fields.Integer(required=True)
    type = fields.String(required=True, validate=validate.OneOf(['next', 'current']))


@app.route('/api/media', methods=['GET'])
@access_token_required
@parse_request_args(SongSchema())
def get_song(user, args):
    room_id = args.get('room_id')
    type = args['type']

    room_participant = RoomParticipant.query \
        .filter(RoomParticipant.room_id == room_id) \
        .filter(RoomParticipant.user_id == user.id) \
        .one_or_none()

    if not room_participant:
        raise Error(StatusCode.FORBIDDEN, message='You are not a member of this room')

    if type == 'next':
        song = get_next_song(room_id)
        res = {
            'message': 'Get next song successfully',
            'data': MediaSchema().dumps(song).data
        }
    elif type == 'current':
        song = get_current_song(room_id)
        res = {
            'message': 'Get current song successfully',
            'data': MediaSchema().dumps(song).data
        }

    return jsonify(res)


def get_next_song(room_id):
    next_song = Media.query \
        .filter(Media.room_id == room_id) \
        .filter(Media.status == MediaStatus.VOTING) \
        .filter(func.max(Media.total_vote)) \
        .first()

    return next_song


def get_current_song(room_id):
    # Calculate time difference since last update
    room = Room.query.filter(Room.id == room_id).one_or_none()
    if room.status == MediaStatus.PAUSING:
        current_media_time = room.media_time
    else:
        time_diff = (datetime.datetime.utcnow() - room.updated).total_seconds()
        current_media_time = room.media_time + time_diff

    current_song = Media.query.filter(Media.id == room.current_media).one_or_none()
    setattr(current_song, 'media_time', current_media_time)
    return current_song


class MediaStatusUpdateSchema(Schema):
    room_id = fields.Integer(required=True)
    status = fields.String(required=True, validate=validate.OneOf([MediaStatus.READY, MediaStatus.SEEKING,
                                                                  MediaStatus.PAUSING, MediaStatus.PLAYING,
                                                                  MediaStatus.FINISHED]))
    media_time = fields.Float(required=True)


@app.route('/api/media/<int:media_id>', methods=['PUT'])
@access_token_required
@parse_request_args(MediaStatusUpdateSchema())
def update_media_status(media_id, user, args):
    room_id = args['room_id']
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
            current_song = get_current_song(room_id)
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
            next_media = get_next_song(room_id)
            room.current_media = next_media.id
            room.media_time = 0
            room.status = MediaStatus.PAUSING
            pusher.trigger(room_id, PusherEvent.PROCEED, MediaSchema().dump(next_media).data)
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


# add new media in the room 
@app.route('/api/media', methods=['POST'])
@parse_request_args(MediaSchema())
@access_token_required
def add_media(**kwargs):
    args = kwargs['args']
    user = kwargs['user']
    if User.get_user_by_email(user.email) is not None: 
        room = db.session.query(Room).filter_by(id=args['room_id'])
        participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=args['room_id']).first()
        if participant is not None: # check whether user is in the room or not to add media
            # check if the url is duplicated 
            all_media = db.session.query(Media).all()
            for media in all_media: 
                if media.url == args['url']: 
                    return jsonify({
                        'message': 'duplicated url'
                    }), StatusCode.FORBIDDEN
            new_media = Media(**args, creator_id=user.id, total_vote=0, status=MediaStatus.ACTIVE)
            db.session.add(new_media)
            db.session.commit()

            return jsonify({
                'message': 'media added to room successfully',
                'media_url': new_media.url,
                'room_id': new_media.room_id,
                'media_id': new_media.id
            })
        raise Error(StatusCode.FORBIDDEN, 'Not allow to add media')
    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')


@app.route('/api/media/<int:media_id>/vote', methods=['POST'])
@access_token_required
def up_vote(media_id, **kwargs):
    user = kwargs['user']
    media = db.session.query(Media).filter_by(id=media_id).first()
    if media is not None: 
        participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=media.room_id).first()
        if participant: # user is in the room that has that media to be able to vote
            vote = db.session.query(Vote).filter_by(user_id=user.id, media_id=media.id).first()
            if vote is None:
                new_vote = Vote(user_id=user.id, media_id=media.id, status=VoteStatus.UPVOTE)
                media.total_vote += 1 # real-time here?
                db.session.add(new_vote)
                db.session.commit()
                return jsonify({
                    'message': 'upvoted successfully', 
                    'current voting media': media.id, 
                    'total vote': media.total_vote  
                })
            if vote.status == VoteStatus.UPVOTE:
                raise Error(StatusCode.FORBIDDEN, 'Already upvoted')
            if vote.status == VoteStatus.DOWNVOTE:
                vote.status = VoteStatus.UPVOTE
                media.total_vote += 1
                db.session.commit()
                return jsonify({
                    'message': 'upvoted successfully', 
                    'current voting media': media.id, 
                    'total vote': media.total_vote  
                })
        raise Error(StatusCode.FORBIDDEN, 'Not allow to vote')
    raise Error(StatusCode.FORBIDDEN, 'Media does not exist')


@app.route('/api/media/<int:media_id>/vote', methods=['DELETE'])
@access_token_required
def down_vote(media_id, **kwargs):
    user = kwargs['user']
    media = db.session.query(Media).filter_by(id=media_id).first()
    if media is not None: 
        participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=media.room_id).first()
        if participant: # user is in the room that has that media to be able to vote
            vote = db.session.query(Vote).filter_by(user_id=user.id, media_id=media.id).first()
            if vote is None:
                raise Error(StatusCode.FORBIDDEN, 'You have to upvote first in order to downvote')
            if vote.status == VoteStatus.DOWNVOTE:
                raise Error(StatusCode.FORBIDDEN, 'Already downvoted')
            if vote.status == VoteStatus.UPVOTE:
                vote.status = VoteStatus.DOWNVOTE
                media.total_vote -= 1
                db.session.commit()
                return jsonify({
                    'message': 'downvoted successfully', 
                    'current voting media': media.id, 
                    'total vote': media.total_vote  
                })
        raise Error(StatusCode.FORBIDDEN, 'Not allow to vote')
    raise Error(StatusCode.FORBIDDEN, 'Media does not exist')


@app.route('/api/media/<int:media_id>', methods=['DELETE'])
@access_token_required
def delete_video(media_id, **kwargs):
    user = kwargs['user']
    media = db.session.query(Media).filter_by(creator_id=user.id, id=media_id).first()
    if media is not None:
        if media.status == MediaStatus.ACTIVE:
            media.status = MediaStatus.DELETED
            db.session.commit()
            return jsonify({
                'message': 'deleted successfully'
            }), 200
    raise Error(StatusCode.BAD_REQUEST, 'Cannot delete media')
