from marshmallow import Schema, fields, validate 


class VoteSchema(Schema):
    id = fields.Int()
    media_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    status = fields.String()