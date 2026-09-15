import asyncio
import time

from app.errors import AppError
from app.models import Confirmation, Trip
from routepilot import optimize_route

from app.observability import log


class TripService:
    def __init__(self, db, provider, timeout):
        self.db, self.provider, self.timeout = db, provider, timeout

    def editable(self, trip_id, token, revision, status=None) -> Trip:
        self.db.authorize(trip_id, token)
        trip = self.db.get(trip_id)
        if trip.revision != revision:
            raise AppError('revision_conflict', '行程已更新，请刷新后重试。', 409)
        if trip.status == 'optimized':
            raise AppError('trip_readonly', '结果已保存；重新规划请创建新行程。', 409)
        if status and trip.status != status:
            raise AppError('invalid_trip_state', '请先解析并确认所有地点。', 409)
        return trip

    async def resolve(self, trip_id, token, revision):
        trip = self.editable(trip_id, token, revision)
        try:
            async with asyncio.timeout(self.timeout):
                async with self.provider.operation() as maps:
                    candidates = [await maps.resolve(p) for p in trip.input.locations()]
        except TimeoutError:
            raise AppError('map_timeout', '地点查询超时，请稍后重试。', 504) from None
        trip.candidates, trip.places, trip.result, trip.status = candidates, [], None, 'resolved'
        return self.db.save(trip, revision)

    def confirm(self, trip_id, token, data: Confirmation):
        trip = self.editable(trip_id, token, data.revision, 'resolved')
        if len(data.candidate_ids) != len(trip.candidates):
            raise AppError('confirmation_incomplete', '请逐个确认所有地点。', 422)
        points = []
        for chosen, candidates in zip(data.candidate_ids, trip.candidates):
            found = next((p for p in candidates if p.candidate_id == chosen), None)
            if found is None:
                raise AppError('invalid_candidate', '地点选择已失效，请重新确认。', 422)
            if any((p.lat, p.lng) == (found.lat, found.lng) or (p.poi_id and p.poi_id == found.poi_id) for p in points):
                raise AppError('duplicate_place', '多个地点指向同一位置，请修改；返回起点请使用返回模式。', 422)
            points.append(found)
        trip.places, trip.status = points, 'confirmed'
        return self.db.save(trip, data.revision)

    async def optimize(self, trip_id, token, revision):
        trip = self.editable(trip_id, token, revision, 'confirmed')
        started = time.monotonic()
        result, segments, warnings = None, [], []
        try:
            async with asyncio.timeout(self.timeout):
                async with self.provider.operation() as maps:
                    matrix = await maps.matrix(trip.places)
                    matrix_ms = round((time.monotonic()-started)*1000)
                    end = len(trip.places)-1 if trip.input.end_mode == 'fixed' else (0 if trip.input.end_mode == 'roundtrip' else None)
                    tick = time.monotonic()
                    try:
                        result = optimize_route(0, list(range(1, len(trip.input.waypoints)+1)), end,
                                                matrix['duration_s'], matrix['distance_m'], trip.input.objective)
                    except (ValueError, KeyError):
                        raise AppError('optimization_failed', '路线成本不完整，未生成结果，请重试。') from None
                    optimization_ms = round((time.monotonic()-tick)*1000, 2)
                    order = result['optimized']['order']
                    # Build every leg before optional geometry: timing out must not drop stops.
                    segments = [{'from_index': a, 'to_index': b,
                                 'distance_m': matrix['distance_m'][a][b], 'duration_s': matrix['duration_s'][a][b],
                                 'polyline': [], 'direction': None} for a, b in zip(order, order[1:])]
                    for index, segment in enumerate(segments):
                        try:
                            direction = await maps.direction(trip.places[segment['from_index']], trip.places[segment['to_index']])
                            segment['polyline'] = direction['polyline']
                            segment['direction'] = {k: v for k, v in direction.items() if k != 'polyline'}
                        except AppError as exc:
                            warnings.append({'segment': index, 'code': exc.code, 'message': exc.message})
        except (TimeoutError, AppError) as exc:
            if result is None:
                if isinstance(exc, AppError):
                    raise
                raise AppError('map_timeout', '路线查询超时，已保留确认地点，请稍后重试。', 504) from None
            # The matrix and order are complete. Keep them when optional route detail fails.
            code = exc.code if isinstance(exc, AppError) else 'map_timeout'
            message = '部分道路详情未取得；已保留全部地点、访问顺序和矩阵成本。'
            warned = {w['segment'] for w in warnings}
            for index, segment in enumerate(segments):
                if not segment['polyline'] and index not in warned:
                    warnings.append({'segment': index, 'code': code, 'message': message})
        result.update(source=matrix['source'], matrix=matrix, segments=segments, warnings=warnings,
                      coordinate_system='GCJ-02', estimate_type='current_batched_snapshot')
        trip.result, trip.status = result, 'optimized'
        saved = self.db.save(trip, revision)
        log('optimized', trip_id=trip_id, matrix_latency_ms=matrix_ms,
            optimization_latency_ms=optimization_ms, chosen_route=order, source=matrix['source'])
        return saved
