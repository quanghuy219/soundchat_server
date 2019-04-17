from marshmallow import Schema, fields, validate 


class RoomParticipantSchema(Schema):
    id = fields.Int()
    name = fields.String()
    user_id = fields.Int()
    room_id = fields.Int()
    media_time = fields.String()
    status = fields.String()
