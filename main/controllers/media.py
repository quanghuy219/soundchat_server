from flask import jsonify
from sqlalchemy import func
from marshmallow import Schema, fields, validate

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room import Room
from main.models.room_paticipant import RoomParticipant
from main.models.media import Media
from main.models.vote import Vote
from main.schemas.media import MediaSchema
from main.libs import media_engine, pusher
from main.enums import MediaStatus, VoteStatus, ParticipantStatus, PusherEvent


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


@app.route('/api/media', methods=['POST'])
@parse_request_args(MediaSchema())
@access_token_required
def add_media(user, args):
    room_id = args['room_id']
    room = db.session.query(Room).filter_by(id=room_id).one_or_none()

    if room is None:
        raise Error(StatusCode.BAD_REQUEST, 'Invalid room id')

    participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=args['room_id']).first()

    # check whether user is in the room or not to add media
    if not participant or participant.status != ParticipantStatus.IN:
        raise Error(StatusCode.FORBIDDEN, 'Not allow to add media')

    new_media = Media(**args, creator_id=user.id, total_vote=1, status=MediaStatus.VOTING)

    db.session.add(new_media)
    db.session.flush()

    pusher.trigger(room_id, PusherEvent.NEW_MEDIA, MediaSchema().dump(new_media).data)

    new_vote = Vote(media_id=new_media.id, user_id=user.id, status=VoteStatus.UPVOTE)
    db.session.add(new_vote)
    db.session.commit()

    # Play the newest proposed video if current_media is not set
    if not room.current_media:
        new_media.status = MediaStatus.PLAYING
        current_media = media_engine.set_current_media(room_id, new_media.id)

        parsed_current_media = MediaSchema().dump(current_media).data
        parsed_current_media['media_time'] = 0
        parsed_current_media['status'] = MediaStatus.PAUSING

        pusher.trigger(room_id, PusherEvent.PROCEED, parsed_current_media)
        media_engine.set_online_users_media_status(room_id, MediaStatus.PAUSING)

    return jsonify({
        'message': 'media added to room successfully',
        'data': MediaSchema().dump(new_media).data
    })


@app.route('/api/media/<int:media_id>/vote', methods=['POST'])
@access_token_required
def up_vote(media_id, **kwargs):
    user = kwargs['user']
    media = db.session.query(Media).filter_by(id=media_id).one_or_none()
    if not media:
        raise Error(StatusCode.FORBIDDEN, 'Media does not exist')

    if media.status != MediaStatus.VOTING:
        raise Error(StatusCode.FORBIDDEN, 'Video cannot be voted')

    room_id = media.room_id
    participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).one_or_none()

    if not participant or participant.status != ParticipantStatus.IN:
        raise Error(StatusCode.FORBIDDEN, 'Video cannot be voted')

    # User is in the room that has that media to be able to vote
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
            'message': 'Upvote successfully',
            'data': MediaSchema().dump(media).data
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
            'message': 'Upvote successfully',
            'data': MediaSchema().dump(media).data
        })


@app.route('/api/media/<int:media_id>/vote', methods=['DELETE'])
@access_token_required
def down_vote(media_id, **kwargs):
    user = kwargs['user']
    media = db.session.query(Media).filter_by(id=media_id).one_or_none()
    if not media:
        raise Error(StatusCode.FORBIDDEN, 'Media does not exist')

    if media.status != MediaStatus.VOTING:
        raise Error(StatusCode.FORBIDDEN, 'Not allow to vote')

    participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=media.room_id).first()
    if participant.status == ParticipantStatus.IN:  # User is in the room that has that media to be able to vote
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
                'data': MediaSchema().dump(media).data
            })


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
                'message': 'deleted successfully',
                'data': MediaSchema().dump(media).data
            }), 200
    raise Error(StatusCode.BAD_REQUEST, 'Cannot delete media')
