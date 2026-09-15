import secrets

from fastapi import APIRouter, Request

from app.models import Trip, TripInput

router = APIRouter(prefix='/api')


@router.get('/config')
def config(request: Request):
    s = request.app.state.settings
    return {'map_mode': s.map_mode, 'tencent_js_key': s.tencent_js_key, 'tencent_nav_key': s.tencent_nav_key}


@router.post('/trips', status_code=201)
def create_trip(data: TripInput, request: Request):
    trip, token = Trip(input=data), secrets.token_urlsafe(32)
    request.app.state.db.create(trip, token)
    return {'trip': trip, 'edit_token': token}


@router.get('/trips/{trip_id}')
def get_trip(trip_id: str, request: Request):
    return request.app.state.db.get(trip_id)
