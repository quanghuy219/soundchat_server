from marshmallow import Schema, fields, validate 


class VoteSchema(Schema):
    id = fields.Int()
    media_id = fields.Int()
    user_id = fields.Int()
    status = fields.String()