import time
from contextlib import asynccontextmanager
from uuid import uuid4
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app.api import router
from app.config import Settings
from app.database import Database
from app.errors import AppError
from app.services.demo import DemoMaps
from app.services.maps import TencentMaps
from app.services.mcp_client import TencentSessionFactory
from app.services.trips import TripService

from app.observability import configure_logging, log, request_id


def create_app(settings: Settings | None = None, provider=None) -> FastAPI:
    settings = settings or Settings.from_env()
    configure_logging()
    db = Database(settings.database_path)
    provider = provider or (DemoMaps() if settings.map_mode == 'demo' else TencentMaps(TencentSessionFactory(settings)))

    @asynccontextmanager
    async def lifespan(app):
        db.initialize()
        yield

    app = FastAPI(title='一趟跑完 · RoutePilot', lifespan=lifespan)
    app.state.settings, app.state.db, app.state.provider = settings, db, provider
    app.state.trips = TripService(db, provider, settings.operation_timeout)

    @app.middleware('http')
    async def request_log(request: Request, call_next):
        request.state.request_id = str(uuid4())
        context_token = request_id.set(request.state.request_id)
        started = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            # Never log exception text: upstream exceptions may contain credential URLs.
            response = error_response(request, 'internal_error', '服务暂时异常，请稍后重试。', 500)
            log('internal_error')
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        log('request', method=request.method, status=response.status_code,
            latency_ms=round((time.monotonic() - started) * 1000))
        request_id.reset(context_token)
        return response

    @app.exception_handler(AppError)
    async def app_error(request, exc):
        log('request_error', code=exc.code, status=exc.status)
        return error_response(request, exc.code, exc.message, exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return error_response(request, 'validation_error', '请检查地点、终点模式和数量（3–8 个途经点）。', 422)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error_response(request, 'http_error', '请求地址或方法不可用。', exc.status_code)

    @app.get('/health')
    def health():
        with db.connect() as conn:
            conn.execute('SELECT 1 FROM trips LIMIT 1')
        return {'status': 'ok'}

    app.include_router(router)
    web = Path(__file__).resolve().parents[1] / 'web'
    app.mount('/web', StaticFiles(directory=web), name='web')

    @app.get('/', include_in_schema=False)
    def index_page():
        return FileResponse(web / 'index.html')

    @app.get('/confirm', include_in_schema=False)
    def confirm_page():
        return FileResponse(web / 'confirm.html')

    @app.get('/t/{trip_id}', include_in_schema=False)
    def result_page(trip_id: str):
        return FileResponse(web / 'result.html')

    return app


def error_response(request, code, message, status):
    return JSONResponse({'error': {'code': code, 'message': message,
                                  'request_id': request.state.request_id}}, status_code=status)


app = create_app()
