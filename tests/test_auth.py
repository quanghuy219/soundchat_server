import json

from tests.helpers import post_data, setup_user


class TestAuthentication:
    def test_user_login_successfully(self, session):
        user = setup_user(session, password='123456')

        data = {
            'email': user.email,
            'password': '123456'
        }
        res = post_data(url='/api/login', data=data)
        assert res.status_code == 200

        res_data = json.loads(res.data)
        assert 'access_token' in res_data

    def test_user_login_with_wrong_email(self, session):
        setup_user(session)

        user_account = {
            'email': 'fake@email.com',
            'password': '123456'
        }
        res = post_data(url='/api/login', data=user_account)
        assert res.status_code == 401

        res_data = json.loads(res.data)
        assert res_data['error_message'] == 'Email or password is incorrect'

    def test_user_login_with_wrong_password(self, session):
        user = setup_user(session)

        data = {
            'email': user.email,
            'password': '123456789'
        }
        res = post_data(url='/api/login', data=data)
        assert res.status_code == 401

        res_data = json.loads(res.data)
        assert res_data['error_message'] == 'Email or password is incorrect'

    def test_user_login_without_email(self, session):
        setup_user(session)

        user_account = {
            'password': '123456789'
        }
        res = post_data(url='/api/login', data=user_account)
        assert res.status_code == 400

        res_data = json.loads(res.data)
        assert 'email' in res_data['error_data']

    def test_user_login_without_password(self, session):
        user = setup_user(session)

        user_account = {
            'email': user.email
        }
        res = post_data(url='/api/login', data=user_account)
        assert res.status_code == 400

        res_data = json.loads(res.data)
        assert 'password' in res_data['error_data']
