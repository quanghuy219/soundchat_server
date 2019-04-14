from flask import jsonify 

from main import db, app 
from main.errors import Error, StatusCode
from main.utils.helpers import parse_request_args, access_token_required
from main.models.room import Room
from main.models.room_paticipant import RoomParticipant
from main.models.user import User
from main.models.message import Message
from main.models.room_playlist import RoomPlaylist
from main.schemas.room import RoomSchema
from main.schemas.message import MessageSchema
from main.schemas.room_playlist import RoomPlaylistSchema
from main.enums import RoomParticipantStatus
from main.schemas.room_participant import RoomParticipantSchema
from main.libs.pusher import _trigger_pusher


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
    room_name = "presence-room-%d" %(args['id'])
    if User.get_user_by_email(user.email) is not None:
        if db.session.query(Room).filter_by(id=args['id']).first() is None:
            new_room = Room(**args, name=room_name, creator_id=user.id)
            db.session.add(new_room)

            # when creator creates the room, he automatically joins that room 
            creator_participant = RoomParticipant(name="room-owner", user_id=user.id, room_id=new_room.id, status=RoomParticipantStatus.ACTIVE)
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
@parse_request_args(RoomParticipantSchema())
@access_token_required
def add_participant_to_room(room_id, **kwargs):
    user = kwargs['user']
    args = kwargs['args']
    name = args['name']
    if User.get_user_by_email(user.email) is not None:
        checked_participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
        if checked_participant is None:
            new_participant = RoomParticipant(name=name, user_id=user.id, room_id=room_id, status=RoomParticipantStatus.ACTIVE)
            room = db.session.query(Room).filter_by(id=room_id).first()
            db.session.add(new_participant)
            db.session.commit()

            notification = {
                "name": name, 
                "user_id": user.id,
                "room": room_id
            }

            _trigger_pusher(room.name, 'new_participant', notification)

            return jsonify({
                'message': 'New participant to the room is created',
                'data': RoomParticipantSchema().dump(new_participant).data
            }), 200
        return jsonify({
            'message': 'Already participated'
        }), StatusCode.FORBIDDEN
    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')


@app.route('/api/rooms/<int:room_id>/users', methods=['DELETE'])
@access_token_required
def delete_participant_in_room(room_id, **kwargs):
    user = kwargs['user']
    if User.get_user_by_email(user.email) is not None: 
        deleted_participant = db.session.query(RoomParticipant).filter_by(user_id=user.id, room_id=room_id).first()
        room = db.session.query(Room).filter_by(id=room_id).first()

        if deleted_participant.status == RoomParticipantStatus.ACTIVE: 
            deleted_participant.status = RoomParticipantStatus.DELETED
            db.session.commit()

            notification = {
                "name": deleted_participant.name, 
                "user_id": user.id,
                "room": room_id
            }

            _trigger_pusher(room.name, 'deleted_participant', notification)

            return jsonify({
                'message': 'Participant deleted successfully'
            }), 200 
        return jsonify({
            'message': 'Failed to delete participant'
        }), 200
    raise Error(StatusCode.UNAUTHORIZED, 'Cannot authorize user')
