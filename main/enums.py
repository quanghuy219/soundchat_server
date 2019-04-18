class UserStatus:
    ACTIVE = 'active'
    DELETED = 'deleted'


class PusherEvent:
    NEW_MESSAGE = 'new_message'
    NEW_PARTICIPANT = 'new_participant'
    DELETE_PARTICIPANT = 'delete_participant'
    PLAY = 'play'
    PAUSE = 'pause'
    SEEK = 'seek'


class RoomParticipantStatus: 
    ACTIVE = 'active'
    DELETED = 'deleted'


class RoomStatus:
    ACTIVE = 'active'
    DELETED = 'deleted'


class MediaStatus:
    VOTING = 'voting'
    PLAYING = 'playing'
    FINISHED = 'finished'


class MediaAction:
    PLAY = 'play'
    PAUSE = 'pause'
    SEEK = 'seek'


MediaActions = [
    MediaAction.PLAY,
    MediaAction.PAUSE,
    MediaAction.SEEK
]
