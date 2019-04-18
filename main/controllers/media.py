from flask import jsonify
from sqlalchemy import func
from marshmallow import Schema, fields, validate

from main import app
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room_paticipant import RoomParticipant
from main.models.media import Media
from main.schemas.media import MediaSchema
from main.enums import MediaStatus, MediaActions


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
