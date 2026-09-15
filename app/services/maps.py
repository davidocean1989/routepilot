"""Typed boundary for GCJ-02 places, directed matrices and driving geometry."""
import math
from contextlib import asynccontextmanager
from typing import Protocol
from uuid import uuid4

from pydantic import ValidationError

from app.errors import AppError
from app.models import LocationInput, Place, now


class MapProvider(Protocol):
    def operation(self): ...
    async def resolve(self, location: LocationInput) -> list[Place]: ...
    async def matrix(self, points: list[Place]) -> dict: ...
    async def direction(self, origin: Place, destination: Place) -> dict: ...


def coord(point: Place) -> str:
    return f'{point.lat},{point.lng}'


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise AppError('map_invalid_cost', '地图返回的路段成本不完整，无法安全计算。')
    return value


def decode_polyline(compressed) -> list[list[float]]:
    if not isinstance(compressed, list) or len(compressed) < 4 or len(compressed) % 2:
        raise AppError('map_invalid_geometry', '地图暂时没有可展示的道路路线。')
    values = compressed[:]
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise AppError('map_invalid_geometry', '地图道路数据不完整。')
    for i in range(2, len(values)):
        values[i] = values[i-2] + values[i] / 1000000
    if any(not -90 <= values[i] <= 90 or not -180 <= values[i+1] <= 180 for i in range(0, len(values), 2)):
        raise AppError('map_invalid_geometry', '地图道路坐标超出范围。')
    return [[values[i], values[i+1]] for i in range(0, len(values), 2)]


def same_city(wanted: str, actual: str) -> bool:
    return not wanted or wanted.removesuffix('市') == actual.removesuffix('市')


class TencentMaps:
    source = 'tencent_mcp'

    def __init__(self, session_factory, caller=None):
        self.session_factory, self.caller = session_factory, caller

    @asynccontextmanager
    async def operation(self):
        async with self.session_factory() as caller:
            yield TencentMaps(self.session_factory, caller)

    async def resolve(self, location: LocationInput) -> list[Place]:
        args = {'keyword': location.query}
        if location.city:
            args['region'] = location.city
        raw = await self.caller.call('placeSuggestion', args)
        entries = raw.get('data', [])
        if not isinstance(entries, list):
            raise AppError('map_invalid_response', '地图地点候选数据格式异常。')
        points = []
        for p in entries[:20]:
            try:
                if not same_city(location.city, p.get('city', '')):
                    continue
                candidate = Place(candidate_id=str(uuid4()), poi_id=str(p['id']) if p.get('id') else None,
                                  name=p['title'], address=p.get('address', ''), city=p.get('city', ''),
                                  lat=p['location']['lat'], lng=p['location']['lng'])
                if not any((q.lat, q.lng, q.name) == (candidate.lat, candidate.lng, candidate.name) for q in points):
                    points.append(candidate)
            except (KeyError, TypeError, ValidationError):
                continue
        if not points:
            raw = await self.caller.call('geocoder', {'address': location.city + location.query})
            p = raw.get('result', {})
            try:
                city = p.get('address_components', {}).get('city', '')
                if same_city(location.city, city):
                    points.append(Place(candidate_id=str(uuid4()), name=location.query,
                                        address=p.get('title') or location.city + location.query, city=city,
                                        lat=p['location']['lat'], lng=p['location']['lng']))
            except (KeyError, TypeError, ValidationError):
                pass
        if not points:
            raise AppError('location_not_found', f'未找到“{location.query}”，请补充城市或更具体的地址。', 422)
        return points[:5]

    async def matrix(self, points: list[Place]) -> dict:
        started = now()
        n, rows, samples = len(points), [], []
        for origin in points:
            sampled_at = now()
            raw = await self.caller.call('matrix', {'from': coord(origin), 'to': ';'.join(map(coord, points)), 'mode': 'driving'})
            try:
                batch = raw['result']['rows']
                if len(batch) != 1 or len(batch[0]['elements']) != n:
                    raise ValueError('matrix dimensions')
                row = batch[0]['elements']
                for e in row:
                    if e.get('status', 0) != 0:
                        raise AppError('route_unreachable', '存在无法通行的路段，请修改地点。')
                    number(e['distance'])
                    number(e['duration'])
                rows.append([{'distance': e['distance'], 'duration': e['duration']} for e in row])
                samples.append({'sampled_at': sampled_at, 'request_id': str(raw.get('request_id', ''))[:200]})
            except (KeyError, TypeError, ValueError, IndexError):
                raise AppError('matrix_incomplete', '地图矩阵缺少路段，未生成优化结果，请重试。') from None
        return {'source': self.source, 'atomic': False, 'started_at': started, 'finished_at': now(),
                'samples': samples, 'point_order': [p.model_dump() for p in points], 'raw_rows': rows,
                'duration_s': [[0 if i == j else rows[i][j]['duration'] for j in range(n)] for i in range(n)],
                'distance_m': [[0 if i == j else rows[i][j]['distance'] for j in range(n)] for i in range(n)]}

    async def direction(self, origin: Place, destination: Place) -> dict:
        raw = await self.caller.call('directionDriving', {'from': coord(origin), 'to': coord(destination)})
        try:
            route = raw['result']['routes'][0]
            return {'polyline': decode_polyline(route['polyline']), 'distance_m': number(route['distance']),
                    'duration_s': number(route['duration']) * 60, 'sampled_at': now()}
        except (KeyError, IndexError, TypeError):
            raise AppError('map_invalid_geometry', '地图暂时没有可展示的道路路线。') from None
