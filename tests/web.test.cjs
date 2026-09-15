const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const context = vm.createContext({URL, URLSearchParams, console});
for (const file of ['common.js', 'navigation.js', 'map.js']) vm.runInContext(fs.readFileSync('web/'+file, 'utf8'), context);
const {RP, Navigation} = context;
const copy = value => JSON.parse(JSON.stringify(value));
const points = [
  {name:'杭州 & 东站',lat:30.291331,lng:120.212998,coordinate_system:'GCJ-02'},
  {name:'乌镇',lat:30.745906,lng:120.48884,coordinate_system:'GCJ-02'},
  {name:'上海',lat:31.194106,lng:121.320666,coordinate_system:'GCJ-02'}
];

test('parse only supported explicit sentence and preserve original order', () => {
  const data = RP.parseSentence('从杭州出发，想去乌镇、西塘古镇、南浔古镇，最后到上海');
  assert.equal(data.start.query, '杭州');
  assert.deepEqual(copy(data.waypoints.map(x=>x.query)), ['乌镇', '西塘古镇', '南浔古镇']);
  assert.equal(data.end.query, '上海');
  assert.equal(RP.parseSentence('推荐几个地方随便安排'), null);
});

test('share URL excludes edit credentials and keeps selected segment', () => {
  const url = RP.shareUrl('https://example.com/confirm?token=SECRET#SECRET', 'abc-123', 2);
  assert.equal(url, 'https://example.com/t/abc-123?segment=2');
});

test('invalid or repeated segment rejected instead of choosing another leg', () => {
  assert.equal(RP.segmentIndex('https://example.com/t/id?segment=1', 2), 1);
  for (const value of ['-1', '2', 'a', '1&segment=0']) {
    assert.throws(()=>RP.segmentIndex('https://example.com/t/id?segment='+value, 2));
  }
});

test('Tencent URI uses selected leg, latitude first, names encoded once', () => {
  const a = new Navigation.TencentMapAdapter('PUBLIC_NAV_KEY');
  const url = new URL(a.buildSegment(points, 0).appUrl);
  assert.equal(url.protocol, 'qqmap:');
  assert.equal(url.hostname, 'map');
  assert.equal(url.pathname, '/routeplan');
  assert.equal(url.searchParams.get('from'), '杭州 & 东站');
  assert.equal(url.searchParams.get('fromcoord'), '30.291331,120.212998');
  assert.equal(url.searchParams.get('tocoord'), '30.745906,120.48884');
  assert.equal(url.searchParams.get('referer'), 'PUBLIC_NAV_KEY');
  assert.equal(a.buildSegment(points, 1).navigationConfirmed, false);
  assert.equal(new URL(a.buildSegment(points, 1).appUrl).searchParams.get('to'), '上海');
});

test('no key, invalid geometry or unsupported provider never create fake links', () => {
  assert.equal(new Navigation.TencentMapAdapter('').buildSegment(points, 0).appUrl, null);
  assert.equal(new Navigation.BaiduMapAdapter().buildSegment(points, 0).appUrl, null);
  assert.equal(new Navigation.AmapAdapter().buildSegment(points, 0).appUrl, null);
  assert.throws(()=>new Navigation.TencentMapAdapter('x').buildSegment(points, 4));
  assert.throws(()=>new Navigation.TencentMapAdapter('x').buildSegment([{...points[0],lat:91}, points[1]], 0));
  assert.equal(new Navigation.TencentMapAdapter('x').buildFullRoute(points).appUrl, null);
});

test('map geometry keeps missing roads absent, demo lines labeled separately', () => {
  const trip = {places: points, result: {source:'tencent_mcp', optimized:{order:[0,1,2]}, segments:[
    {polyline:[[30.2,120.2],[30.7,120.4]]}, {polyline:[]}
  ]}};
  assert.equal(context.RouteMap.geometryData(trip).roads.length, 1);
  assert.equal(context.RouteMap.geometryData(trip).schematic.length, 0);
  trip.result.source = 'historical_demo';
  assert.equal(context.RouteMap.geometryData(trip).schematic.length, 3);
});

test('signed savings explain tradeoff rather than claiming both improve', () => {
  assert.match(RP.savingsText(-600, 'time'), /增加/);
  assert.match(RP.savingsText(600, 'time'), /节省/);
  assert.match(RP.savingsText(0, 'distance'), /相同/);
});

test('SDK adapter builds numbered markers, true road geometry, bounds and escaped information', async () => {
  const captures = {};
  class LatLng { constructor(lat,lng) {this.lat=lat;this.lng=lng;} }
  class Map { constructor(container,options){ captures.center=options.center; } fitBounds(bounds){captures.bounds=bounds;} }
  class MultiMarker { constructor(options){captures.markers=options.geometries;} on(name,fn){captures.click=fn;} }
  class MultiPolyline { constructor(options){captures.lines=options.geometries;} }
  class PolylineStyle { constructor(options){} }
  class LatLngBounds { constructor(){this.points=[];} extend(point){this.points.push(point);} }
  class InfoWindow { close(){} setContent(content){assert.equal(typeof content,'string');captures.info=content;} setPosition(){} open(){} }
  const elements = {map:{hidden:false},'map-status':{textContent:''}};
  const ctx = vm.createContext({console,TMap:{LatLng,Map,MultiMarker,MultiPolyline,PolylineStyle,LatLngBounds,InfoWindow},
    document:{getElementById:id=>elements[id],createElement:()=>({textContent:''})}});
  vm.runInContext(fs.readFileSync('web/map.js','utf8'),ctx);
  const trip={places:points.map(p=>({...p,address:'<img onerror=alert(1)>'})),result:{source:'tencent_mcp',optimized:{order:[0,1,2]},segments:[{polyline:[[30,120],[30.1,120.1]]},{polyline:[]}]}};
  await ctx.RouteMap.render(trip,'PUBLIC_KEY');
  assert.equal(captures.markers.length,3);
  assert.deepEqual(copy(captures.markers.map(m=>m.content)),['1','2','3']);
  assert.equal(captures.lines.length,1);
  assert.equal(captures.lines[0].paths[1].lat,30.1);
  assert.equal(captures.bounds.points.length,5);
  captures.click({geometry:{id:'0'}});
  assert.match(captures.info, /&lt;img onerror=alert/);
  assert.match(elements['map-status'].textContent,/部分道路/);
  assert.equal(elements.map.hidden,false);
});

test('missing SDK key keeps map hidden with clear guidance', async () => {
  const elements={map:{hidden:false},'map-status':{textContent:''}};
  const ctx=vm.createContext({document:{getElementById:id=>elements[id]}});
  vm.runInContext(fs.readFileSync('web/map.js','utf8'),ctx);
  await ctx.RouteMap.render({},'');
  assert.equal(elements.map.hidden,true);
  assert.match(elements['map-status'].textContent,/暂未启用/);
});
