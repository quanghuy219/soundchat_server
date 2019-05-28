from flask import jsonify
from sqlalchemy import func
from marshmallow import Schema, fields, validate

from main import db, app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room import Room
from main.models.room_participant import RoomParticipant
from main.models.video import Video
from main.models.vote import Vote
from main.schemas.video import VideoSchema
from main.libs import video_engine, pusher
from main.enums import VideoStatus, VoteStatus, ParticipantStatus, PusherEvent


class NextSongSchema(Schema):
    room_id = fields.Integer(required=True)


@app.route('/api/videos', methods=['GET'])
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

    song = Video.query \
        .filter(Video.room_id == room_id) \
        .filter(Video.status == VideoStatus.VOTING) \
        .filter(func.max(Video.total_vote)) \
        .first()
    res = {
        'message': 'Get next song successfully',
        'data': VideoSchema.dumps(song).data
    }
    return jsonify(res)


@app.route('/api/videos', methods=['POST'])
@parse_request_args(VideoSchema())
@access_token_required
def add_video(user, args):
    room_id = args['room_id']
    room = db.session.query(Room).filter_by(id=room_id).one_or_none()

    if room is None:
        raise Error(StatusCode.BAD_REQUEST, 'Invalid room id')

    participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=args['room_id']).first()

    # check whether user is in the room or not to add video
    if not participant or participant.status != ParticipantStatus.IN:
        raise Error(StatusCode.FORBIDDEN, 'Not allow to add video')

    new_video = Video(**args, creator_id=user.id, total_vote=1, status=VideoStatus.VOTING)

    db.session.add(new_video)
    db.session.flush()

    pusher.trigger(room_id, PusherEvent.NEW_VIDEO, VideoSchema().dump(new_video).data)

    new_vote = Vote(video_id=new_video.id, user_id=user.id, status=VoteStatus.UPVOTE)
    db.session.add(new_vote)
    db.session.commit()

    # Play the newest proposed video if current_video is not set
    if not room.current_video:
        new_video.status = VideoStatus.PLAYING
        current_video = video_engine.set_current_video(room_id, new_video.id)

        parsed_current_video = VideoSchema().dump(current_video).data
        parsed_current_video['video_time'] = 0
        parsed_current_video['status'] = VideoStatus.PAUSING

        pusher.trigger(room_id, PusherEvent.PROCEED, parsed_current_video)
        video_engine.set_online_users_video_status(room_id, VideoStatus.PAUSING)

    return jsonify({
        'message': 'Video added to room successfully',
        'data': VideoSchema().dump(new_video).data
    })


@app.route('/api/videos/<int:video_id>/vote', methods=['POST'])
@access_token_required
def up_vote(video_id, **kwargs):
    user = kwargs['user']
    video = db.session.query(Video).filter_by(id=video_id).one_or_none()
    if not video:
        raise Error(StatusCode.FORBIDDEN, 'Video does not exist')

    if video.status != VideoStatus.VOTING:
        raise Error(StatusCode.FORBIDDEN, 'Video cannot be voted')

    room_id = video.room_id
    participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).one_or_none()

    if not participant or participant.status != ParticipantStatus.IN:
        raise Error(StatusCode.FORBIDDEN, 'Video cannot be voted')

    # User is in the room that has that video to be able to vote
    vote = db.session.query(Vote).filter_by(user_id=user.id, video_id=video.id).first()
    if vote is None:
        new_vote = Vote(user_id=user.id, video_id=video.id, status=VoteStatus.UPVOTE)
        video.total_vote += 1
        db.session.add(new_vote)
        db.session.commit()

        data = {
            "name": user.name,
            "id": video.id,
            "total_vote": video.total_vote
        }

        pusher.trigger(video.room_id, PusherEvent.UP_VOTE, data)

        return jsonify({
            'message': 'Upvote successfully',
            'data': VideoSchema().dump(video).data
        })
    if vote.status == VoteStatus.UPVOTE:
        raise Error(StatusCode.FORBIDDEN, 'Already up-voted')

    if vote.status == VoteStatus.DOWNVOTE:
        vote.status = VoteStatus.UPVOTE
        video.total_vote += 1
        db.session.commit()

        data = {
            "name": user.name,
            "id": video.id,
            "total_vote": video.total_vote
        }

        pusher.trigger(video.room_id, PusherEvent.UP_VOTE, data)

        return jsonify({
            'message': 'Upvote successfully',
            'data': VideoSchema().dump(video).data
        })


@app.route('/api/videos/<int:video_id>/vote', methods=['DELETE'])
@access_token_required
def down_vote(video_id, **kwargs):
    user = kwargs['user']
    video = db.session.query(Video).filter_by(id=video_id).one_or_none()
    if not video:
        raise Error(StatusCode.FORBIDDEN, 'Video does not exist')

    if video.status != VideoStatus.VOTING:
        raise Error(StatusCode.FORBIDDEN, 'Not allow to vote')

    participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=video.room_id).first()
    if participant.status == ParticipantStatus.IN:  # User is in the room that has that video to be able to vote
        vote = db.session.query(Vote).filter_by(user_id=user.id, video_id=video.id).first()
        if vote is None:
            raise Error(StatusCode.FORBIDDEN, 'You have to up-vote first in order to down-vote')
        if vote.status == VoteStatus.DOWNVOTE:
            raise Error(StatusCode.FORBIDDEN, 'Already down-voted')
        if vote.status == VoteStatus.UPVOTE:
            vote.status = VoteStatus.DOWNVOTE
            video.total_vote -= 1
            db.session.commit()
            data = {
                "name": user.name,
                "id": video.id,
                "total_vote": video.total_vote
            }

            pusher.trigger(video.room_id, PusherEvent.DOWN_VOTE, data)

            return jsonify({
                'message': 'Down-voted successfully',
                'data': VideoSchema().dump(video).data
            })


@app.route('/api/videos/<int:video_id>', methods=['DELETE'])
@access_token_required
def delete_video(video_id, **kwargs):
    user = kwargs['user']
    video = db.session.query(Video).filter_by(creator_id=user.id, id=video_id).first()
    if video is not None:
        if video.status == VideoStatus.ACTIVE:
            video.status = VideoStatus.DELETED
            db.session.commit()
            return jsonify({
                'message': 'Deleted successfully',
                'data': VideoSchema().dump(video).data
            }), 200
    raise Error(StatusCode.BAD_REQUEST, 'Cannot delete video')
