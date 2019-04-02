from marshmallow import Schema, fields, validate 


class MessageSchema(Schema):
    id = fields.Int()
    user_id = fields.Int(required=True)
    room_id = fields.Int(required=True)
    content = fields.String(validate=validate.Length(min=1, max=140), required=True)
    status = fields.String()
