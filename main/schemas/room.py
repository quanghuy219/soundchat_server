from marshmallow import Schema, fields, validate 


class RoomSchema(Schema):
    id = fields.Int()
    name = fields.Str(validate=validate.Length(min=3, max=50), required=True)
    creator_id = fields.Int()
    current_media = fields.Int(required=False)
    status = fields.Str(validate=validate.Length(min=3, max=20))
