import datetime

from sqlalchemy import desc

from main.models.room_participant import RoomParticipant
from main.models.video import Video
from main.models.room import Room
from main.enums import VideoStatus, ParticipantStatus
from main import db


def get_next_video(room_id):
    next_video = Video.query \
        .filter(Video.room_id == room_id) \
        .filter(Video.status == VideoStatus.VOTING) \
        .order_by(desc(Video.total_vote)) \
        .first()

    return next_video


def get_current_video(room_id):
    # Calculate time difference since last update
    room = Room.query.filter(Room.id == room_id).one_or_none()
    if room.current_video is None:
        return None

    if room.status == VideoStatus.PAUSING:
        current_video_time = room.video_time
    else:
        time_diff = (datetime.datetime.utcnow() - room.updated).total_seconds()
        current_video_time = room.video_time + time_diff

    current_video = Video.query.filter(Video.id == room.current_video).one_or_none()
    current_video.status = room.status
    setattr(current_video, 'video_time', current_video_time)
    return current_video


def set_current_video(room_id, current_video_id=None, video_time=0, status=VideoStatus.PAUSING):
    """
    Set current video for a room
    """
    if current_video_id is None:
        next_video = get_next_video(room_id)
        if next_video is not None:
            next_video.status = VideoStatus.PLAYING
            current_video_id = next_video.id

    room = Room.query.filter(Room.id == room_id).one_or_none()
    room.current_video = current_video_id
    room.video_time = video_time
    room.status = status
    db.session.commit()

    current_video = get_current_video(room_id)
    return current_video


def check_all_user_have_same_video_status(room_id, status):
    not_ready_users = RoomParticipant.query \
                        .filter(RoomParticipant.room_id == room_id) \
                        .filter(RoomParticipant.status == ParticipantStatus.IN) \
                        .filter(RoomParticipant.video_status != status) \
                        .all()

    if not len(not_ready_users):
        return True

    return False


def set_online_users_video_status(room_id, status):
    online_users = RoomParticipant.query \
                        .filter(RoomParticipant.room_id == room_id) \
                        .filter(RoomParticipant.status == ParticipantStatus.IN) \
                        .all()

    if not len(online_users):
        return

    for user in online_users:
        user.video_status = status

    db.session.commit()
