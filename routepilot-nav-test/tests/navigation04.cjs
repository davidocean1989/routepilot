const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');const ctx={URL,URLSearchParams};vm.createContext(ctx);
if(fs.existsSync('dist/navigation04.js'))vm.runInContext(fs.readFileSync('dist/navigation04.js','utf8'),ctx);
assert.ok(ctx.Navigation04,'NavigationAdapter must be available');
const n=ctx.Navigation04, trip=n.trip;
for(const os of ['ios','android'])for(const provider of ['tencent','baidu','amap']){
 const a=n.adapter(provider,os,'test-key');
 for(let i=0;i<4;i++){
  const link=a.buildSegment(trip,i);assert.ok(link.appUrl);assert.ok(link.webUrl.startsWith('https://'));
  assert.equal(link.pointCount,2);assert.equal(link.navigationConfirmed,false);
 }
 assert.throws(()=>a.buildSegment(trip,4));
 const full=a.buildFullRoute(trip);
 if(provider==='amap'){
  const p=new URL(full.appUrl).searchParams;
  assert.equal(p.get('vian'),'3');assert.equal(p.get('vialons'),'120.48884|120.430771|120.888689');
  assert.equal(p.get('slat'),'30.291331');assert.equal(p.get('dlon'),'121.320666');
  assert.equal(new URL(full.appUrl).protocol,os==='ios'?'iosamap:':'amapuri:');
 }else if(provider==='baidu'&&os==='android'){
  const p=new URL(full.appUrl).searchParams;assert.equal(p.get('coord_type'),'gcj02');
  const v=JSON.parse(p.get('viaPoints')).viaPoints;assert.equal(v.length,3);assert.equal(v[0].lng,120.48884);assert.equal(v[2].lat,30.93898);
 }else assert.equal(full.appUrl,null);
 assert.equal(full.productionEnabled,false);
}
assert.equal(new URL(n.adapter('amap','ios').buildSegment(trip,0).webUrl).searchParams.get('from'),'120.212998,30.291331,杭州东站');
assert.equal(new URL(n.adapter('baidu','android').buildSegment(trip,0).appUrl).protocol,'bdapp:');
assert.throws(()=>n.adapter('tencent','ios','').buildSegment(trip,0));
assert.equal(n.parseShare('https://test.example/spike04.html?trip_id=rp-spike04-demo-v1&segment=2').segment,2);
assert.throws(()=>n.parseShare('https://test.example/spike04.html?trip_id=unknown'));
assert.throws(()=>n.parseShare('https://test.example/spike04.html?trip_id=rp-spike04-demo-v1&trip_id=other'));
assert.throws(()=>n.parseShare('https://test.example/spike04.html?segment=99'));
const share=new URL(n.shareUrl('https://test.example/spike04.html?noise=1#x',trip.trip_id,3));
assert.equal(share.searchParams.get('trip_id'),'rp-spike04-demo-v1');assert.equal(share.searchParams.get('segment'),'3');assert.equal(share.hash,'');
console.log('PASS: 24 segment links, OS schemes, ordered full-route payloads, unsupported routes, unknown/duplicate trip IDs, share continuity. No phone navigation tested.');
assert.equal(n.parseShare('https://example.test/spike04?provider=baidu').provider,'baidu');
assert.equal(n.parseShare('https://example.test/spike04').provider,'amap');
assert.throws(()=>n.parseShare('https://example.test/spike04?provider=unknown'));
assert.equal(new URL(n.shareUrl('https://example.test/spike04',trip.trip_id,2,'tencent')).searchParams.get('provider'),'tencent');
