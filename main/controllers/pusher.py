from flask import request, jsonify, render_template

from main import app
from main.utils.helpers import access_token_required
from main.libs.pusher import authenticate, _trigger_new_message, _trigger_pusher
from main.errors import Error


@app.route('/pusher/auth', methods=['POST'])
@access_token_required
def authenticate_user(user):
    res = authenticate(request, user)
    if not res:
        raise Error(status_code=400, message='Bad Request')

    return jsonify(res)


@app.route('/api/testing')
def testing():
    _trigger_new_message('presence-room-1', {'message': 'Hello world'})
    
    return jsonify({})
