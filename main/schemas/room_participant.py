from marshmallow import Schema, fields, validate

from main.schemas.user import UserSchema


class RoomParticipantSchema(Schema):
    id = fields.Int()
    user_id = fields.Int()
    user = fields.Nested(UserSchema)
    room_id = fields.Int()
    media_time = fields.String()
    status = fields.String()
