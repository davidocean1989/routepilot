import asyncio
import json
from contextlib import asynccontextmanager

import pytest

from app.errors import AppError
from app.models import LocationInput, Place
from app.services.mcp_client import ToolCaller, unpack_response
from app.services.maps import TencentMaps, decode_polyline


def envelope(data, is_error=False):
    return {'content': [{'type': 'text', 'text': json.dumps(data)}], 'is_error': is_error}


class Session:
    def __init__(self, responses):
        self.responses, self.calls = iter(responses), []

    async def call_tool(self, name, arguments, **kwargs):
        self.calls.append((name, arguments))
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return envelope(value)


async def no_sleep(seconds):
    pass


def point(i):
    return Place(candidate_id=str(i), name='地点' + str(i), address='地址', lat=30+i/10, lng=120+i/10)


def provider(responses):
    session = Session(responses)

    @asynccontextmanager
    async def factory():
        yield ToolCaller(session, interval=0, sleep=no_sleep)

    return TencentMaps(factory), session


def test_unpack_business_error_even_when_mcp_success():
    with pytest.raises(AppError) as e:
        unpack_response(envelope({'status': 120, 'message': 'secret URL'}))
    assert e.value.code == 'map_rate_limited'
    assert 'secret' not in e.value.message


@pytest.mark.parametrize('response', [
    {'content': [{'type': 'text', 'text': 'not json'}]},
    envelope({'status': 0}, True), envelope({'result': {}}),
    envelope({'status': False, 'result': {}}),
])
def test_reject_malformed_envelopes(response):
    with pytest.raises(AppError):
        unpack_response(response)


def test_invalid_key_never_retries():
    session = Session([{'status': 311, 'message': 'Invalid Key SECRET'}])
    with pytest.raises(AppError):
        asyncio.run(ToolCaller(session, interval=0, sleep=no_sleep).call('matrix', {}))
    assert len(session.calls) == 1


def test_rate_limit_retries_and_recovers():
    session = Session([{'status': 120}, {'status': 120}, {'status': 0, 'result': {}}])
    assert asyncio.run(ToolCaller(session, interval=0, sleep=no_sleep).call('matrix', {}))['status'] == 0
    assert len(session.calls) == 3


def test_timeout_is_bounded_and_safe():
    session = Session([TimeoutError('SECRET')] * 3)
    with pytest.raises(AppError) as e:
        asyncio.run(ToolCaller(session, interval=0, sleep=no_sleep).call('matrix', {}))
    assert e.value.status == 504 and 'SECRET' not in str(e.value)
    assert len(session.calls) == 3


def test_matrix_preserves_direction_and_normalizes_only_diagonal():
    maps, session = provider([
        {'status': 0, 'request_id': 'r1', 'result': {'rows': [{'elements': [{'distance': 12, 'duration': 3}, {'distance': 200, 'duration': 20}]}]}},
        {'status': 0, 'request_id': 'r2', 'result': {'rows': [{'elements': [{'distance': 400, 'duration': 50}, {'distance': 4, 'duration': 60}]}]}},
    ])
    async def run():
        async with maps.operation() as p:
            return await p.matrix([point(0), point(1)])
    result = asyncio.run(run())
    assert result['distance_m'] == [[0, 200], [400, 0]]
    assert result['duration_s'] == [[0, 20], [50, 0]]
    assert result['atomic'] is False
    assert len(result['samples']) == 2
    assert result['raw_rows'][0][0]['distance'] == 12
    assert session.calls[0][1] == {'from': '30.0,120.0', 'to': '30.0,120.0;30.1,120.1', 'mode': 'driving'}


@pytest.mark.parametrize('rows', [[], [{'elements': []}], [{'elements': [{'distance': 0, 'duration': 0}, {'distance': None, 'duration': 5}]}], [{'elements': [{'distance': 0, 'duration': 0}, {'distance': 1, 'duration': -1}]}]])
def test_missing_invalid_matrix_fails_closed(rows):
    maps, _ = provider([{'status': 0, 'result': {'rows': rows}}])
    async def run():
        async with maps.operation() as p:
            await p.matrix([point(0), point(1)])
    with pytest.raises(AppError):
        asyncio.run(run())


def test_directions_convert_minutes_and_decode_polyline_without_mutation():
    compressed = [30.0, 120.0, 100000, 100000]
    maps, _ = provider([{'status': 0, 'result': {'routes': [{'distance': 200, 'duration': 2.5, 'polyline': compressed}]}}])
    async def run():
        async with maps.operation() as p:
            return await p.direction(point(0), point(1))
    result = asyncio.run(run())
    assert result['duration_s'] == 150
    assert result['polyline'] == [[30, 120], [30.1, 120.1]]
    assert compressed == [30, 120, 100000, 100000]


@pytest.mark.parametrize('value', [[30], [30, 120, 1], [91, 120, 0, 0], [30, 120, float('nan'), 0]])
def test_invalid_polyline(value):
    with pytest.raises(AppError):
        decode_polyline(value)


def test_candidates_not_automatically_selected_and_city_filter():
    maps, session = provider([{'status': 0, 'data': [
        {'id': 'a', 'title': '国贸', 'address': '北京', 'city': '北京市', 'location': {'lat': 39, 'lng': 116}},
        {'id': 'b', 'title': '国贸', 'address': '上海', 'city': '上海市', 'location': {'lat': 31, 'lng': 121}},
    ]}])
    async def run():
        async with maps.operation() as p:
            return await p.resolve(LocationInput(query='国贸', city='北京'))
    result = asyncio.run(run())
    assert len(result) == 1 and result[0].poi_id == 'a'
    assert session.calls[0][1] == {'keyword': '国贸', 'region': '北京'}
