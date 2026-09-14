"""Validate saved, redacted MCP evidence without network access."""
import json, re, hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
runs=[json.loads((R/f).read_text()) for f in ['live-probe.json','recovery-probe.json']]
events=[]
for run in runs:
    assert not run.get('error'), run.get('error')
    for e in run['events']:
        b=json.loads(e['response']['content'][0]['text'])
        events.append({'case':e['case'],'elapsed_ms':e['elapsed_ms'],'mcp_is_error':e['response']['is_error'],'status':b['status'],'message':b['message'],'body':b})
assert all(e['status']==120 for e in events if e['case'] in ('matrix-5x5','matrix-5x5-retry'))
rows=[]
for i in range(5):
    e=next(e for e in events if e['case']==f'matrix-row-{i}')
    assert e['status']==0 and not e['mcp_is_error']
    rr=e['body']['result']['rows']; assert len(rr)==1 and len(rr[0]['elements'])==5
    rows.append(rr[0]['elements'])
for row in rows:
    for v in row:
        assert v.get('status',0)==0 and isinstance(v['distance'],(int,float)) and isinstance(v['duration'],(int,float)) and v['distance']>=0 and v['duration']>=0
pairs=[{'i':i,'j':j,'forward':rows[i][j],'reverse':rows[j][i]} for i in range(5) for j in range(i+1,5) if rows[i][j]!=rows[j][i]]
success=[e['elapsed_ms'] for e in events if e['status']==0]
summary={'status':'PARTIAL','authentication':'PASS','single_request_5x5':'BLOCKED_BY_STATUS_120','assembled_5x5':'PASS','assembly':'five sequential 1x5 calls, not atomic; historical POI coordinates reused','valid_cells':25,'valid_non_diagonal_edges':20,'asymmetric_pairs':pairs,'raw_diagonal':[rows[i][i] for i in range(5)],'distance_unit':'meter (official documentation)','duration_unit':'second (official documentation)','successful_call_count':len(success),'success_latency_ms':{'min':min(success),'max':max(success),'mean':round(sum(success)/len(success),2)},'events':[{k:v for k,v in e.items() if k!='body'} for e in events]}
(R/'verification-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(R/'assembled-matrix.json').write_text(json.dumps({'point_order':['杭州','南浔古镇','乌镇','西塘古镇','上海'],'distance_unit':'m','duration_unit':'s','rows':rows,'source':'recovery-probe.json, matrix-row-0 through matrix-row-4','atomic':False},ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
