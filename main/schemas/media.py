from marshmallow import Schema, fields, validate 


class MediaSchema(Schema):
    id = fields.Int()
    creator_id = fields.Int()
    room_id = fields.Int(required=True)
    url = fields.URL()
    total_vote = fields.Int()

    media_time = fields.Float()
    is_voted = fields.Boolean()
    status = fields.String()


