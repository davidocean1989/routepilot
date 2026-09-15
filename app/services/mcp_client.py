"""Bounded Tencent MCP calls. No credential URL or upstream text in logs/errors."""
import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from urllib.parse import urlencode

from app.errors import AppError

logger = logging.getLogger('routepilot')


def unpack_response(response) -> dict:
    if hasattr(response, 'model_dump'):
        response = response.model_dump(mode='json')
    if not isinstance(response, dict):
        raise AppError('map_invalid_response', '地图服务返回了无法读取的数据。')
    raw = response.get('structured_content', response.get('structuredContent'))
    if raw is None:
        texts = [p.get('text', '') for p in response.get('content', []) if isinstance(p, dict) and p.get('type') == 'text']
        if len(texts) != 1:
            raise AppError('map_invalid_response', '地图服务返回了无法读取的数据。')
        if 'Invalid Key' in texts[0]:
            raise AppError('map_auth_error', '地图服务凭证无效，请联系服务维护者。', 503)
        try:
            raw = json.loads(texts[0])
        except (ValueError, TypeError):
            raise AppError('map_invalid_response', '地图服务返回了无法读取的数据。') from None
    if not isinstance(raw, dict) or type(raw.get('status')) is not int:
        raise AppError('map_invalid_response', '地图服务响应缺少业务状态。')
    status = raw['status']
    if status in (120, 429):
        raise AppError('map_rate_limited', '地图服务请求繁忙，请稍后重试。', 503)
    if status in (110, 111, 112, 311):
        raise AppError('map_auth_error', '地图服务凭证或权限不可用，请联系服务维护者。', 503)
    if status != 0 or response.get('is_error', response.get('isError', False)):
        raise AppError('map_business_error', '地图服务未能完成查询，请检查地点后重试。')
    return raw


class ToolCaller:
    def __init__(self, session, interval=5.0, sleep=asyncio.sleep):
        self.session, self.interval, self.sleep = session, interval, sleep
        self.last_call = 0.0

    async def call(self, name: str, arguments: dict) -> dict:
        for attempt in range(3):
            await self.sleep(max(0.0, self.interval - (time.monotonic() - self.last_call)))
            self.last_call = time.monotonic()
            try:
                result = await self.session.call_tool(name, arguments, read_timeout_seconds=20)
                data = unpack_response(result)
                logger.info(json.dumps({'event': 'map_call', 'tool': name, 'attempt': attempt,
                                        'latency_ms': round((time.monotonic()-self.last_call)*1000)}))
                return data
            except AppError as exc:
                if exc.code != 'map_rate_limited' or attempt == 2:
                    raise
            except Exception as exc:
                # SDK v2 uses httpx2; inspect only status, never propagate URLs.
                status = getattr(getattr(exc, 'response', None), 'status_code', None)
                if status is not None and status != 429 and status < 500:
                    raise AppError('map_http_error', '地图服务拒绝了请求。') from None
                if attempt == 2:
                    if isinstance(exc, TimeoutError) or 'timeout' in type(exc).__name__.lower():
                        raise AppError('map_timeout', '地图服务响应超时，请稍后重试。', 504) from None
                    raise AppError('map_unavailable', '暂时无法连接地图服务，请稍后重试。', 503) from None
            await self.sleep(max(self.interval, 1.0) * (attempt + 1))
        raise AssertionError('unreachable')


def find_app_error(exc):
    if isinstance(exc, AppError):
        return exc
    for nested in getattr(exc, 'exceptions', []):
        error = find_app_error(nested)
        if error:
            return error
    return None


class TencentSessionFactory:
    def __init__(self, settings):
        self.settings = settings
        self.lock = asyncio.Lock()
        self.last_finish = 0.0

    @asynccontextmanager
    async def __call__(self):
        if not self.settings.tencent_map_key:
            raise AppError('map_not_configured', '地图服务尚未配置，请联系服务维护者。', 503)
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        # These transport loggers may include query-string credentials on errors.
        for name in ('httpx', 'httpx2', 'httpcore', 'httpcore2', 'mcp.client.sse', 'mcp.shared.session'):
            logging.getLogger(name).disabled = True
        async with self.lock:
            await asyncio.sleep(max(0, self.settings.map_interval - (time.monotonic()-self.last_finish)))
            url = 'https://mcp.map.qq.com/sse?' + urlencode({'key': self.settings.tencent_map_key, 'format': 1})
            try:
                # Both the SSE context and ClientSession enter/exit in the calling task.
                async with sse_client(url, timeout=12, sse_read_timeout=25) as (read, write):
                    async with ClientSession(read, write, read_timeout_seconds=20) as session:
                        await session.initialize()
                        yield ToolCaller(session, self.settings.map_interval)
            except Exception as exc:
                error = find_app_error(exc)
                if error:
                    raise error from None
                raise AppError('map_unavailable', '地图连接暂时不可用，请稍后重试。', 503) from None
            finally:
                self.last_finish = time.monotonic()
