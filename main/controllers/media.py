from flask import jsonify
from sqlalchemy import func
from marshmallow import Schema, fields, validate

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room import Room
from main.models.room_paticipant import RoomParticipant
from main.models.user import User
from main.models.media import Media
from main.models.vote import Vote
from main.schemas.media import MediaSchema
from main.enums import MediaStatus, VoteStatus, MediaActions


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

    if not room_participant:
        raise Error(StatusCode.FORBIDDEN, message='You are not a member of this room')

    song = Media.query\
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
