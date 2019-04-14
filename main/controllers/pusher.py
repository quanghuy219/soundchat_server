from flask import request, jsonify, render_template

from main import app
from main.utils.helpers import access_token_required
from main.libs.pusher import authenticate
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
    return render_template('pusher.html')