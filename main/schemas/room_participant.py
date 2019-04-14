from marshmallow import Schema, fields, validate 


class RoomParticipantSchema(Schema):
    id = fields.Int()
    name = fields.String()
    user_id = fields.Int()
    room_id = fields.Int()
    status = fields.String()

    