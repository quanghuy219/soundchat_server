class UserStatus:
    ACTIVE = 'active'
    DELETED = 'deleted'


class PusherEvent:
    NEW_MESSAGE = 'new_message'
    NEW_PARTICIPANT = 'new_participant'
    DELETE_PARTICIPANT = 'delete_participant'


class RoomParticipantStatus: 
    ACTIVE = 'active'
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
