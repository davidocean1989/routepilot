"""Live MCP probe. Optional Key from TENCENT_MAP_KEY; never persisted."""
import asyncio
import json
import logging
import os
import platform
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlencode

from mcp import ClientSession
from mcp.client.sse import sse_client

logging.disable(logging.CRITICAL)
ROOT = Path(__file__).resolve().parent
KEY = os.environ.get('TENCENT_MAP_KEY', '')
def now():
    return datetime.now(timezone.utc).isoformat()

record = {'started_at': now(), 'environment': {'os': platform.platform(),
          'python': platform.python_version(), 'mcp': version('mcp')},
          'endpoint': 'https://mcp.map.qq.com/sse?key=<REDACTED>&format=1',
          'authenticated': bool(KEY), 'events': [],
          'coordinate_source': '../points.json (historical POIs, not refreshed)'}

async def main():
    try:
        async with asyncio.timeout(55):
            url = 'https://mcp.map.qq.com/sse?' + urlencode({'key': KEY, 'format': 1})
            async with sse_client(url, timeout=12, sse_read_timeout=20) as (r, w):
                async with ClientSession(r, w) as session:
                    for method in ('initialize', 'list_tools'):
                        t = time.monotonic()
                        result = await getattr(session, method)()
                        record[method] = {'elapsed_ms': round((time.monotonic()-t)*1000, 2),
                                          'response': result.model_dump(mode='json')}
                    points = json.loads((ROOT.parent / 'points.json').read_text())
                    coords = [str(p['location']['lat'])+','+str(p['location']['lng']) for p in points]
                    cases = [('matrix-1x1-forward', 'matrix', {'from': coords[0], 'to': coords[1], 'mode': 'driving'}),
                             ('matrix-1x1-reverse', 'matrix', {'from': coords[1], 'to': coords[0], 'mode': 'driving'}),
                             ('matrix-5x5', 'matrix', {'from': ';'.join(coords), 'to': ';'.join(coords), 'mode': 'driving'})]
                    for case, tool, args in cases:
                        event = {'case': case, 'tool': tool, 'arguments': args, 'sent_at': now()}
                        t = time.monotonic()
                        response = await session.call_tool(tool, args)
                        event.update(elapsed_ms=round((time.monotonic()-t)*1000, 2), response=response.model_dump(mode='json'))
                        record['events'].append(event)
                        await asyncio.sleep(2)
    except Exception as exc:
        record['error'] = repr(exc)
    finally:
        record['finished_at'] = now()
        content = json.dumps(record, ensure_ascii=False, indent=2)
        if KEY:
            content = content.replace(KEY, '<REDACTED>')
        (ROOT / 'live-probe.json').write_text(content)
        print(json.dumps({'events': len(record['events']), 'error': record.get('error'), 'file': str(ROOT/'live-probe.json')}))

asyncio.run(main())
