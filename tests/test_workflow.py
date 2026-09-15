from dataclasses import replace

from fastapi.testclient import TestClient

from app.main import create_app
from app.database import Database
from app.errors import AppError
from app.models import Trip, TripInput
from test_api import client, settings, payload


def new(client):
    data = client.post('/api/trips', json=payload()).json()
    return '/api/trips/' + data['trip']['trip_id'], {'X-Trip-Token': data['edit_token']}


def resolve_confirm(client, path, headers):
    r = client.post(path+'/resolve', json={'revision': 0}, headers=headers)
    assert r.status_code == 200, r.text
    trip = r.json()
    assert trip['status'] == 'resolved'
    r = client.post(path+'/confirm', json={'revision': trip['revision'], 'candidate_ids': [p[0]['candidate_id'] for p in trip['candidates']]}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_demo_end_to_end_and_persistent_readonly_snapshot(client, settings):
    path, headers = new(client)
    trip = resolve_confirm(client, path, headers)
    r = client.post(path+'/optimize', json={'revision': trip['revision']}, headers=headers)
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['status'] == 'optimized'
    assert result['result']['optimized']['total_duration'] == 12954
    assert result['result']['optimized']['total_distance'] == 229985
    assert result['result']['original']['total_duration'] == 15912
    assert len(result['result']['segments']) == 4
    assert result['result']['source'] == 'historical_demo'
    assert result['result']['segments'][0]['polyline'] == []
    assert client.post(path+'/resolve', json={'revision': result['revision']}, headers=headers).status_code == 409
    with TestClient(create_app(settings)) as other:
        assert other.get(path).json() == result


def test_shortest_and_open_roundtrip(client):
    for mode in ['fixed', 'open', 'roundtrip']:
        body = payload() | {'objective': 'shortest', 'end_mode': mode}
        if mode != 'fixed': body['end'] = None
        data = client.post('/api/trips', json=body).json()
        path, headers = '/api/trips/'+data['trip']['trip_id'], {'X-Trip-Token': data['edit_token']}
        trip = resolve_confirm(client, path, headers)
        r = client.post(path+'/optimize', json={'revision': trip['revision']}, headers=headers)
        assert r.status_code == 200, r.text
        result = r.json()['result']
        if mode == 'fixed': assert result['optimized']['total_distance'] == 219289
        if mode == 'roundtrip': assert result['optimized']['order'][0] == result['optimized']['order'][-1]
        if mode == 'open': assert len(result['optimized']['order']) == 4


def test_unauthorized_and_unconfirmed(client):
    path, headers = new(client)
    assert client.post(path+'/resolve', json={'revision': 0}).status_code == 403
    assert client.post(path+'/optimize', json={'revision': 0}, headers=headers).status_code == 409
    assert client.get(path).json()['status'] == 'draft'


def test_forged_candidate_and_stale_revision(client):
    path, headers = new(client)
    t = client.post(path+'/resolve', json={'revision': 0}, headers=headers).json()
    assert client.post(path+'/confirm', json={'revision': t['revision'], 'candidate_ids': ['fake']*5}, headers=headers).status_code == 422
    assert client.post(path+'/resolve', json={'revision': 0}, headers=headers).status_code == 409
    assert client.get(path).json()['status'] == 'resolved'


def test_missing_demo_location_never_substitutes(client):
    data = client.post('/api/trips', json=payload() | {'start': {'query': '不存在的地方'}}).json()
    path, headers = '/api/trips/'+data['trip']['trip_id'], {'X-Trip-Token': data['edit_token']}
    r = client.post(path+'/resolve', json={'revision': 0}, headers=headers)
    assert r.status_code == 422
    assert client.get(path).json()['status'] == 'draft'


def test_duplicate_places_rejected(client):
    body = payload()
    body['waypoints'][1] = body['waypoints'][0]
    data = client.post('/api/trips', json=body).json()
    path, headers = '/api/trips/'+data['trip']['trip_id'], {'X-Trip-Token': data['edit_token']}
    t = client.post(path+'/resolve', json={'revision': 0}, headers=headers).json()
    r = client.post(path+'/confirm', json={'revision': t['revision'], 'candidate_ids': [p[0]['candidate_id'] for p in t['candidates']]}, headers=headers)
    assert r.status_code == 422


def test_real_mode_without_key_does_not_fallback(settings):
    with TestClient(create_app(replace(settings, map_mode='tencent'))) as c:
        path, headers = new(c)
        r = c.post(path+'/resolve', json={'revision': 0}, headers=headers)
        assert r.status_code == 503
        assert c.get(path).json()['status'] == 'draft'


def test_database_compare_and_swap(settings):
    import pytest
    db = Database(settings.database_path)
    db.initialize()
    t = Trip(input=TripInput.model_validate(payload()))
    db.create(t, 'token')
    db.save(t, 0)
    with pytest.raises(AppError) as e:
        db.save(t, 0)
    assert e.value.status == 409


def test_matrix_failure_does_not_change_confirmed_trip(settings):
    from app.services.demo import DemoMaps
    class BrokenMaps(DemoMaps):
        async def matrix(self, points):
            raise AppError('matrix_incomplete', '缺少路段')
    with TestClient(create_app(settings, provider=BrokenMaps())) as c:
        path, headers = new(c)
        before = resolve_confirm(c, path, headers)
        r = c.post(path+'/optimize', json={'revision': before['revision']}, headers=headers)
        assert r.status_code == 502
        assert c.get(path).json() == before


def test_timeout_does_not_save_partial_result(settings):
    import asyncio
    from app.services.demo import DemoMaps
    class SlowMaps(DemoMaps):
        async def matrix(self, points):
            await asyncio.sleep(1)
    with TestClient(create_app(replace(settings, operation_timeout=.01), provider=SlowMaps())) as c:
        path, headers = new(c)
        before = resolve_confirm(c, path, headers)
        r = c.post(path+'/optimize', json={'revision': before['revision']}, headers=headers)
        assert r.status_code == 504
        assert c.get(path).json() == before


def test_geometry_failure_keeps_real_optimization_and_warning(client):
    path, headers = new(client)
    trip = resolve_confirm(client, path, headers)
    result = client.post(path+'/optimize', json={'revision': trip['revision']}, headers=headers).json()['result']
    assert result['optimized']['total_duration'] == 12954
    assert len(result['warnings']) == 4
    assert all(s['polyline'] == [] for s in result['segments'])


def test_reresolve_invalidates_previous_candidates(client):
    path, headers = new(client)
    t = client.post(path+'/resolve', json={'revision': 0}, headers=headers).json()
    old_ids = [p[0]['candidate_id'] for p in t['candidates']]
    t = client.post(path+'/resolve', json={'revision': 1}, headers=headers).json()
    r = client.post(path+'/confirm', json={'revision': t['revision'], 'candidate_ids': old_ids}, headers=headers)
    assert r.status_code == 422


def test_geometry_timeout_preserves_completed_optimization(settings):
    import asyncio
    from app.services.demo import DemoMaps
    class SlowDirections(DemoMaps):
        async def direction(self, origin, destination):
            await asyncio.sleep(1)
    with TestClient(create_app(replace(settings, operation_timeout=.02), provider=SlowDirections())) as c:
        path, headers = new(c)
        trip = resolve_confirm(c, path, headers)
        r = c.post(path+'/optimize', json={'revision': trip['revision']}, headers=headers)
        assert r.status_code == 200, r.text
        result = r.json()['result']
        assert result['optimized']['total_duration'] == 12954
        assert len(result['segments']) == 4
        assert all(s['polyline'] == [] for s in result['segments'])
        assert all(w['code'] == 'map_timeout' for w in result['warnings'])
