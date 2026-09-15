"""HTTP smoke against a running local server. No credentials or private addresses."""
import json
import sys
import urllib.request

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765'

def call(path, body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['X-Trip-Token'] = token
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=190) as r:
        return json.load(r)

assert call('/health') == {'status': 'ok'}
data = call('/api/trips', {'start': {'query': '杭州'}, 'waypoints': [{'query': q} for q in ['乌镇', '西塘古镇', '南浔古镇']], 'end': {'query': '上海'}})
path = '/api/trips/' + data['trip']['trip_id']
assert call(path) == data['trip']
print('PASS: health, create, retrieve')
if '--full' in sys.argv:
    token = data['edit_token']
    trip = call(path + '/resolve', {'revision': 0}, token)
    trip = call(path + '/confirm', {'revision': trip['revision'], 'candidate_ids': [p[0]['candidate_id'] for p in trip['candidates']]}, token)
    trip = call(path + '/optimize', {'revision': trip['revision']}, token)
    assert trip['status'] == 'optimized' and len(trip['result']['segments']) == 4
    assert call(path) == trip
    print('PASS: resolve, confirm, optimize, reload; mode=' + trip['result']['source'])
