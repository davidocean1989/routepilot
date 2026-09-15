"""Explicit opt-in replay of archived Tencent data; never a live fallback."""
import json
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from app.errors import AppError
from app.models import Place, now
from app.services.maps import same_city

ROOT = Path(__file__).resolve().parents[2]


class DemoMaps:
    source = 'historical_demo'

    def __init__(self):
        self.points = json.loads((ROOT/'docs/spike-02-evidence/points.json').read_text())
        self.snapshot = json.loads((ROOT/'docs/spike-02-evidence/supplement-2026-09-14/assembled-matrix.json').read_text())

    @asynccontextmanager
    async def operation(self):
        yield self

    async def resolve(self, location):
        aliases = [['杭州', '杭州东站'], ['南浔', '南浔古镇'], ['乌镇'], ['西塘', '西塘古镇'], ['上海', '上海虹桥站']]
        for i, p in enumerate(self.points):
            if location.query in [*aliases[i], p['title']] and same_city(location.city, p['city']):
                return [Place(candidate_id=str(uuid4()), poi_id=p['id'], name=p['title'], address=p['address'], city=p['city'], **p['location'])]
        raise AppError('demo_location_unavailable', f'演示样本不包含“{location.query}”，请使用示例地点或切换真实服务。', 422)

    async def matrix(self, points):
        indices = [next(i for i, p in enumerate(self.points) if p['id'] == place.poi_id) for place in points]
        rows = [[self.snapshot['rows'][i][j].copy() for j in indices] for i in indices]
        n = len(points)
        return {'source': self.source, 'atomic': False,
                'started_at': '2026-09-14T08:52:55Z', 'finished_at': '2026-09-14T08:53:16Z',
                'replayed_at': now(), 'raw_rows': rows, 'point_order': [p.model_dump() for p in points],
                'duration_s': [[0 if i == j else rows[i][j]['duration'] for j in range(n)] for i in range(n)],
                'distance_m': [[0 if i == j else rows[i][j]['distance'] for j in range(n)] for i in range(n)]}

    async def direction(self, origin, destination):
        raise AppError('demo_geometry_unavailable', '历史演示仅有成本矩阵，不包含本条道路折线。')
