import logging
import os
import json

from main import pusher_client
from main.libs.tasks import celery_app


def parse_channel_name(channel_name):
    """Channel name format: presence-room-<room_id>"""
    with open('pusher_namespace.json') as namespace_file:
        data = json.load(namespace_file)
        namespace = data['namespace']

    return channel_name + '-' + namespace


def authenticate(request, account):
    try:
        auth = pusher_client.authenticate(
            channel=request.form['channel_name'],
            socket_id=request.form['socket_id'],
            custom_data={
                'user_id': account.id
            }
        )
    except Exception:
        logging.exception('Pusher authentication exception')
        return None

    return auth


@celery_app.task
def _trigger_pusher(channel_name, event, data):
    try:
        pusher_client.trigger(channel_name, event, data)
    except Exception:
        logging.exception('Pusher exception occurs')


def trigger(channel_name, event, data):
    if os.getenv('FLASK_ENV') == 'test':
        return _trigger_pusher(parse_channel_name(channel_name), event, data)

    return _trigger_pusher.delay(parse_channel_name(channel_name), 'new_message', data)


def trigger_new_message(channel_name, data):
    return trigger(channel_name, 'new_message', data)
