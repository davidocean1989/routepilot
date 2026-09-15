import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def payload():
    return {
        'start': {'query': '杭州'},
        'waypoints': [{'query': name} for name in ['乌镇', '西塘古镇', '南浔古镇']],
        'end': {'query': '上海'}, 'end_mode': 'fixed', 'objective': 'fastest',
    }


@pytest.fixture
def settings(tmp_path):
    return Settings(database_path=str(tmp_path / 'trips.sqlite3'), map_mode='demo')


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


def test_create_and_read_after_restart(settings):
    with TestClient(create_app(settings)) as c:
        assert c.get('/health').json() == {'status': 'ok'}
        response = c.post('/api/trips', json=payload())
        assert response.status_code == 201
        data = response.json()
        assert data['trip']['status'] == 'draft'
        assert len(data['edit_token']) >= 32
    with TestClient(create_app(settings)) as c:
        response = c.get('/api/trips/' + data['trip']['trip_id'])
        assert response.status_code == 200
        assert response.json() == data['trip']
        assert data['edit_token'] not in response.text
        assert 'token_hash' not in response.text


@pytest.mark.parametrize('change', [
    {'waypoints': [{'query': 'a'}] * 2},
    {'waypoints': [{'query': 'a'}] * 9},
    {'start': {'query': '  '}}, {'objective': 'whatever'},
    {'end': None}, {'end_mode': 'open'},
    {'start': {'query': 'x' * 201}}, {'unexpected': True},
])
def test_invalid_trip(client, change):
    response = client.post('/api/trips', json=payload() | change)
    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'
    assert response.json()['error']['request_id'] == response.headers['x-request-id']


def test_missing_trip(client):
    assert client.get('/api/trips/missing').status_code == 404


def test_open_and_roundtrip(client):
    for mode in ['open', 'roundtrip']:
        response = client.post('/api/trips', json=payload() | {'end': None, 'end_mode': mode})
        assert response.status_code == 201


def test_config_does_not_leak_server_key(tmp_path):
    s = Settings(database_path=str(tmp_path / 'db'), tencent_map_key='SERVER_SECRET')
    with TestClient(create_app(s)) as c:
        assert 'SERVER_SECRET' not in c.get('/api/config').text


def test_database_does_not_store_plain_token(client, settings):
    from pathlib import Path
    data = client.post('/api/trips', json=payload()).json()
    assert data['edit_token'].encode() not in Path(settings.database_path).read_bytes()
