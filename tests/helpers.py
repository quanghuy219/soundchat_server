import random
import json

from main import app
from main.models.user import User


def random_id():
    return random.randint(1, 1000)


def random_email():
    email = 'test_{}@test.com'.format(random_id())

    while User.get_user_by_email(email) is not None:
        email = 'test_{}@test.com'.format(random_id())

    return email


def setup_user(session, email=None, password='123456', name='Testing User'):
    """Set up a mock account"""
    if email is None:
        email = random_email()

    user = User(name=name, email=email, password=password)
    session.add(user)
    session.commit()
    return user


test_app = app.test_client()


def post_data(url, data, token=''):
    headers = {'Authorization': 'Bearer {}'.format(token)}
    return test_app.post(url, headers=headers, data=json.dumps(data), content_type='application/json')


def put_data(url, data, token=''):
    headers = {'Authorization': 'Bearer {}'.format(token)}
    return test_app.put(url, headers=headers, data=json.dumps(data), content_type='application/json')


def delete_data(url, data=None, token=''):
    headers = {'Authorization': 'Bearer {}'.format(token)}
    return test_app.delete(url, headers=headers, data=json.dumps(data), content_type='application/json')


def get_data(url, token=''):
    headers = {'Authorization': 'Bearer {}'.format(token)}
    return test_app.get(url, headers=headers)
