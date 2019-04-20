class UserStatus:
    ACTIVE = 'active'
    DELETED = 'deleted'


class PusherEvent:
    NEW_MESSAGE = 'new_message'
    NEW_PARTICIPANT = 'new_participant'
    EXIT_PARTICIPANT = 'exit_participant'
    DELETE_PARTICIPANT = 'delete_participant'
    NEW_MEDIA = 'new_media'
    PLAY = 'play'
    PAUSE = 'pause'
    SEEK = 'seek'
    PROCEED = 'proceed'


class ParticipantStatus:
    IN = 'in'
    OUT = 'out'
    DELETED = 'deleted'


class RoomStatus:
    ACTIVE = 'active'
    DELETED = 'deleted'


class VoteStatus: 
    UPVOTE = 'upvote'
    DOWNVOTE = 'downvote'


class MediaStatus: 
    ACTIVE = 'active'
    DELETED = 'deleted'
    VOTING = 'voting'
    PLAYING = 'playing'
    FINISHED = 'finished'
    PAUSING = 'pausing'
    READY = 'ready'
    SEEKING = 'seeking'


class MediaAction:
    PLAY = 'play'
    PAUSE = 'pause'
    SEEK = 'seek'


MediaActions = [
    MediaAction.PLAY,
    MediaAction.PAUSE,
    MediaAction.SEEK
]
