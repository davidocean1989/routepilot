'use strict';
globalThis.RouteMap = (() => {
  function geometryData(trip) {
    return {roads:trip.result.segments.filter(s => s.polyline.length>1).map(s=>s.polyline),
      schematic:trip.result.source==='historical_demo' ? trip.result.optimized.order.map(i=>[trip.places[i].lat,trip.places[i].lng]) : []};
  }
  let sdkPromise;
  function loadSDK(key) {
    if (globalThis.TMap) return Promise.resolve(globalThis.TMap);
    if (!sdkPromise) sdkPromise = new Promise((resolve,reject) => {
      const script = document.createElement('script');
      const timer = setTimeout(() => reject(Error('地图加载超时，可稍后重试。')), 15000);
      script.src = 'https://map.qq.com/api/gljs?v=1.exp&key='+encodeURIComponent(key);
      script.onload = () => { clearTimeout(timer); globalThis.TMap ? resolve(globalThis.TMap) : reject(Error('地图未能初始化。')); };
      script.onerror = () => { clearTimeout(timer); reject(Error('地图暂时无法加载，请检查网络。')); };
      document.head.append(script);
    }).catch(e => {sdkPromise=undefined; throw e;});
    return sdkPromise;
  }
  async function render(trip, key) {
    const container = document.getElementById('map'), notice = document.getElementById('map-status');
    if (!key) { notice.textContent='地图暂未启用，完整地点与分段路线仍可在下方查看。'; container.hidden=true; return; }
    try {
      notice.textContent = '正在加载地图…';
      const TMap = await loadSDK(key);
      container.hidden=false;
      const order = trip.result.optimized.order, points=order.map(i=>trip.places[i]);
      const coords=points.map(p=>new TMap.LatLng(p.lat,p.lng));
      const map = new TMap.Map(container,{center:coords[0],zoom:9,pitch:0});
      const markers = new TMap.MultiMarker({map,geometries:coords.map((position,i)=>({id:String(i),position,content:String(i+1)}))});
      const info = new TMap.InfoWindow({map,position:coords[0],content:''}); info.close();
      markers.on('click', event => {
        const i = Number(event.geometry.id);
        const text = `${i+1}. ${points[i].name} · ${points[i].address}`;
        const escaped = text.replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
        info.setContent(escaped); info.setPosition(coords[i]); info.open();
      });
      const data = geometryData(trip);
      const geometries = data.roads.map((line,i)=>({id:'road'+i,styleId:'road',paths:line.map(p=>new TMap.LatLng(...p))}));
      if (data.schematic.length) geometries.push({id:'schematic',styleId:'demo',paths:data.schematic.map(p=>new TMap.LatLng(...p))});
      if (geometries.length) new TMap.MultiPolyline({map,styles:{road:new TMap.PolylineStyle({color:'#147d64',width:7,showArrow:true}),
        demo:new TMap.PolylineStyle({color:'#777f76',width:3,dashArray:[8,8]})},geometries});
      const all = [...coords,...geometries.flatMap(g=>g.paths)];
      const bounds=new TMap.LatLngBounds(all[0],all[0]); all.forEach(p=>bounds.extend(p));
      map.fitBounds(bounds,{padding:50});
      notice.textContent=data.schematic.length ? '虚线仅表示访问顺序，不是实际道路。' : (data.roads.length===trip.result.segments.length ? '道路路线为地图查询结果；导航 App 会按当时路况重新计算。' : '部分道路路线暂缺；地点和已取得的路段仍可查看。');
    } catch (e) { notice.textContent=e.message+' 完整行程仍保留在下方。'; container.hidden=true; }
  }
  return {geometryData, render};
})();
