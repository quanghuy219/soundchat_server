from marshmallow import Schema, fields, validate, ValidationError
from marshmallow.decorators import validates


class UserSchema(Schema):
    id = fields.Int()
    name = fields.String(validate=validate.Length(min=3, max=50), required=True)
    email = fields.Email(validate=validate.Length(min=3, max=255), required=True)
    password = fields.String(validate=validate.Length(min=5, max=10), load_only=True, required=True)

    @validates('password')
    def validate_password(self, password):
        flag = True
        if ' ' in password:
            flag = False
        if not any(char.isdigit() for char in password):
            flag = False

        if not flag:
            raise ValidationError('Password must contain at least 1 digit, and white space is not allowed', 'password')
