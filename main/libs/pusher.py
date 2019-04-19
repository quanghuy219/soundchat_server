import logging
import os

from main import pusher_client
from main.libs.tasks import celery_app
from main.cfg import config


def parse_channel_name(room_id):
    """Channel name format: presence-room-<room_id>-<namespace>"""
    return "presence-room-{}-{}".format(room_id, config.PUSHER_NAMESPACE)


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


def trigger(room_id, event, data={}):
    if os.getenv('FLASK_ENV') == 'test':
        return _trigger_pusher(parse_channel_name(room_id), event, data)

    return _trigger_pusher.delay(parse_channel_name(room_id), event, data)
