from flask import jsonify
from sqlalchemy import func
from marshmallow import Schema, fields, validate

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room_paticipant import RoomParticipant
from main.models.user import User
from main.models.media import Media
from main.models.vote import Vote
from main.schemas.media import MediaSchema

from main.enums import MediaStatus, VoteStatus, MediaActions, ParticipantStatus, PusherEvent
from main.libs import pusher


class NextSongSchema(Schema):
    room_id = fields.Integer(required=True)


@app.route('/api/media', methods=['GET'])
@access_token_required
@parse_request_args(NextSongSchema())
def get_next_song(user, args):
    room_id = args.get('room_id')
    room_participant = RoomParticipant.query \
        .filter(RoomParticipant.room_id == room_id) \
        .filter(RoomParticipant.user_id == user.id) \
        .one_or_none()

    if room_participant.status is not ParticipantStatus.IN:
        raise Error(StatusCode.FORBIDDEN, message='You are not a member of this room')

    song = Media.query \
        .filter(Media.room_id == room_id) \
        .filter(Media.status == MediaStatus.VOTING) \
        .filter(func.max(Media.total_vote)) \
        .first()
    res = {
        'message': 'Get next song successfully',
        'data': MediaSchema.dumps(song).data
    }
    return jsonify(res)


# add new media in the room 
@app.route('/api/media', methods=['POST'])
@parse_request_args(MediaSchema())
@access_token_required
def add_media(**kwargs):
    args = kwargs['args']
    user = kwargs['user']
    if User.get_user_by_email(user.email) is not None: 
        participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=args['room_id']).first()
        if participant.status == ParticipantStatus.IN:
            # check whether user is in the room or not to add media
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
    if media.status == MediaStatus.ACTIVE: 
        participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=media.room_id).first()
        if participant.status == ParticipantStatus.IN:
            # user is in the room that has that media to be able to vote
            vote = db.session.query(Vote).filter_by(user_id=user.id, media_id=media.id).first()
            if vote is None:
                new_vote = Vote(user_id=user.id, media_id=media.id, status=VoteStatus.UPVOTE)
                media.total_vote += 1
                db.session.add(new_vote)
                db.session.commit()

                data = {
                    "name": user.name,
                    "media": media.id,
                    "total_vote": media.total_vote
                }

                pusher.trigger(media.room_id, PusherEvent.UP_VOTE, data)

                return jsonify({
                    'message': 'up-voted successfully',
                    'current_media': media.id, 
                    'total_vote': media.total_vote  
                })
            if vote.status == VoteStatus.UPVOTE:
                raise Error(StatusCode.FORBIDDEN, 'Already up-voted')
            if vote.status == VoteStatus.DOWNVOTE:
                vote.status = VoteStatus.UPVOTE
                media.total_vote += 1
                db.session.commit()

                data = {
                    "name": user.name,
                    "media": media.id,
                    "total_vote": media.total_vote
                }

                pusher.trigger(media.room_id, PusherEvent.UP_VOTE, data)

                return jsonify({
                    'message': 'up-voted successfully',
                    'current_media': media.id, 
                    'total_vote': media.total_vote  
                })
        raise Error(StatusCode.FORBIDDEN, 'Not allow to vote')
    raise Error(StatusCode.FORBIDDEN, 'Media does not exist')


@app.route('/api/media/<int:media_id>/vote', methods=['DELETE'])
@access_token_required
def down_vote(media_id, **kwargs):
    user = kwargs['user']
    media = db.session.query(Media).filter_by(id=media_id).first()
    if media.status == MediaStatus.ACTIVE: 
        participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=media.room_id).first()
        if participant.status == ParticipantStatus.IN:  # user is in the room that has that media to be able to vote
            vote = db.session.query(Vote).filter_by(user_id=user.id, media_id=media.id).first()
            if vote is None:
                raise Error(StatusCode.FORBIDDEN, 'You have to up-vote first in order to down-vote')
            if vote.status == VoteStatus.DOWNVOTE:
                raise Error(StatusCode.FORBIDDEN, 'Already down-voted')
            if vote.status == VoteStatus.UPVOTE:
                vote.status = VoteStatus.DOWNVOTE
                media.total_vote -= 1
                db.session.commit()
                data = {
                    "name": user.name,
                    "media": media.id,
                    "total_vote": media.total_vote
                }

                pusher.trigger(media.room_id, PusherEvent.DOWN_VOTE, data)

                return jsonify({
                    'message': 'down-voted successfully',
                    'current_media': media.id, 
                    'total_vote': media.total_vote  
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
