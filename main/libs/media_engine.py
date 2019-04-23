import datetime

from sqlalchemy import desc

from main.models.room_paticipant import RoomParticipant
from main.models.media import Media
from main.models.room import Room
from main.enums import MediaStatus, ParticipantStatus
from main import db


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
    current_song.status = room.status
    setattr(current_song, 'media_time', current_media_time)
    return current_song


def set_current_media(room_id, current_media_id=None, media_time=0, status=MediaStatus.PAUSING):
    """
    Set current video for a room
    """
    if current_media_id is None:
        next_media = get_next_media(room_id)
        if next_media is not None:
            current_media_id = next_media.id

    room = Room.query.filter(Room.id == room_id).one_or_none()
    room.current_media = current_media_id
    room.media_time = media_time
    room.status = status
    db.session.commit()

    current_media = get_current_media(room_id)
    return current_media


def check_all_user_have_same_media_status(room_id, status):
    not_ready_users = RoomParticipant.query \
                        .filter(RoomParticipant.room_id == room_id) \
                        .filter(RoomParticipant.status == ParticipantStatus.IN) \
                        .filter(RoomParticipant.media_status != status) \
                        .all()

    if not len(not_ready_users):
        return True

    return False


def set_online_users_media_status(room_id, status):
    online_users = RoomParticipant.query \
                        .filter(RoomParticipant.room_id == room_id) \
                        .filter(RoomParticipant.status == ParticipantStatus.IN) \
                        .all()

    if not len(online_users):
        return

    for user in online_users:
        user.media_status = status

    db.session.commit()
