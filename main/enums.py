class UserStatus:
    ACTIVE = 'active'
    DELETED = 'deleted'


class PusherEvent:
    NEW_MESSAGE = 'new_message'
    NEW_PARTICIPANT = 'new_participant'
    EXIT_PARTICIPANT = 'exit_participant'
    DELETE_PARTICIPANT = 'delete_participant'
    UP_VOTE = 'up_vote'
    DOWN_VOTE = 'down_vote'
    NEW_MEDIA = 'new_media'
    MEDIA_STATUS_CHANGED = 'media_status_changed'
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


class VideoStatus:
    ACTIVE = 'active'
    DELETED = 'deleted'
    VOTING = 'voting'
    PLAYING = 'playing'
    FINISHED = 'finished'
    PAUSING = 'pausing'
    READY = 'ready'
    SEEKING = 'seeking'


class VideoAction:
    PLAY = 'play'
    PAUSE = 'pause'
    SEEK = 'seek'


VideoActions = [
    VideoAction.PLAY,
    VideoAction.PAUSE,
    VideoAction.SEEK
]
