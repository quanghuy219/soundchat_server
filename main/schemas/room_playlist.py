from marshmallow import Schema, fields, validate 


class RoomPlaylistSchema(Schema):   
    id = fields.Int()
    room_id = fields.Int(required=True)
    media_id = fields.Int(required=True)
    status = fields.String()