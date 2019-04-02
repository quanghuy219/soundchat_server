import logging

from pusher.errors import PusherError

from main import pusher_client


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
    except PusherError:
        logging.exception('Pusher authentication exception')
        return None

    return auth


def _trigger_pusher(channel_name, event, data):
    try:
        pusher_client.trigger(channel_name, event, data)
    except PusherError:
        logging.exception('Pusher exception occurs')
