import logging
import os

from main import pusher_client
from main.libs.tasks import celery_app


def parse_channel_name(channel_name):
    """Channel name format: presence-room-<room_id>"""
    channel = channel_name.split('-')
    if len(channel) != 3:
        return None

    return {
        'room': channel[2]
    }


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
        return _trigger_pusher(channel_name, event, data)

    return _trigger_pusher.delay(channel_name, 'new_message', data)


def trigger_new_message(channel_name, data):
    return trigger(channel_name, 'new_message', data)
