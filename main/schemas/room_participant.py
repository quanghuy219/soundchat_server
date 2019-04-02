from marshmallow import Schema, fields, validate 


class RoomParticipantSchema(Schema):
    id = fields.Int()
    name = fields.String()
    user_id = fields.Int(required=True)
    room_id = fields.Int(required=True)
    status = fields.String()

    