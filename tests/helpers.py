import random
import json

from main import app
from main.models.user import UserModel


def random_id():
    return random.randint(1, 1000)


def random_email():
    email = 'test_{}@test.com'.format(random_id())

    while UserModel.get_account_by_email(email) is not None:
        email = 'test_{}@test.com'.format(random_id())

    return email


def setup_user(session, email=None, password='123456', name='Testing User'):
    """Set up a mock account"""
    if email is None:
        email = random_email()

    account = UserModel(name=name, email=email, password=password)
    session.add(account)
    session.commit()
    return account


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
