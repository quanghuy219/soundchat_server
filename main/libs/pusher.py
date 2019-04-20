import logging
import os

from main import pusher_client
from main.libs.tasks import celery_app
from main.cfg import config


def create_channel_name(room_id):
    """Channel name format: presence-room-<room_id>-<namespace>"""
    return "presence-room-{}-{}".format(room_id, config.PUSHER_NAMESPACE)


def parse_channel_name(channel_name):
    """Read room id from channel name"""
    names = channel_name.split('-')
    if len(names) != 4:
        logging.warning('Invalid pusher channel name')
        return None

    return names[2]


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
        return _trigger_pusher(create_channel_name(room_id), event, data)

    return _trigger_pusher.delay(create_channel_name(room_id), event, data)


def read_pusher_webhook(request):
    webhook = pusher_client.validate_webhook(
        key=request.headers.get('X-Pusher-Key'),
        signature=request.headers.get('X-Pusher-Signature'),
        body=request.data
    )
    return webhook
