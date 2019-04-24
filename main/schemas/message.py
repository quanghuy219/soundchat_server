from marshmallow import Schema, fields, validate

from main.schemas.user import UserSchema


class MessageSchema(Schema):
    id = fields.Int()
    user_id = fields.Int()
    user = fields.Nested(UserSchema)
    room_id = fields.Int(required=True)
    content = fields.String(validate=validate.Length(min=1, max=140), required=True)
    status = fields.String()
