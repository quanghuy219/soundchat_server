from marshmallow import Schema, fields, validate 


class MediaSchema(Schema):
    id = fields.Int()
    creator_id = fields.Int()
    room_id = fields.Int(required=True)
    url = fields.URL(required=True)
    total_vote = fields.Int()
    status = fields.String()


