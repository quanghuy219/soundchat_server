from marshmallow import Schema, fields, validate 


class RoomSchema(Schema):
    id = fields.Int()
    creator_id = fields.Int()
    current_media = fields.Int(required=False)
    media_time = fields.Int()
    fingerprint = fields.String()
    status = fields.Str(validate=validate.Length(min=3, max=20))
