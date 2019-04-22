import json

from tests.helpers import post_data, get_data, setup_user, setup_room
from main.utils.helpers import encode
from main.enums import ParticipantStatus


class TestRoom:
    def test_create_room_successfully(self, session):
        user = setup_user(session)
        token = encode(user)
        res = post_data('/api/rooms', {}, token)
        assert res.status_code == 200
        res_data = json.loads(res.data)
        assert res_data['message'] == 'New room is created'
        room_info = res_data['data']

        res = get_data('/api/rooms/{}'.format(room_info['id']), token)
        assert res.status_code == 200
        data = json.loads(res.data)['data']
        participants = data['participants']
        assert len(participants) == 1
        assert participants[0]['user_id'] == user.id
        assert participants[0]['status'] == ParticipantStatus.IN

    def test_get_room_list(self, session):
        user = setup_user(session)
        token = encode(user)
        room = setup_room(session, user.id)
        res = get_data('/api/rooms', token)
        assert res.status_code == 200
        res_data = json.loads(res.data)['data']
        assert len(res_data) == 1
        assert res_data[0]['id'] == room.id
