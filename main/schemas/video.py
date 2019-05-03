from marshmallow import Schema, fields, validate 


class VideoSchema(Schema):
    id = fields.Int()
    creator_id = fields.Int()
    room_id = fields.Int(required=True)
    url = fields.URL(required=True)
    total_vote = fields.Int()

    video_time = fields.Float()
    is_voted = fields.Boolean()
    status = fields.String()


