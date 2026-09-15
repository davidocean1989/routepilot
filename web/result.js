'use strict';
(() => {
  const {$,el}=RP;
  let trip,config,index=0,points;
  const id=decodeURIComponent(location.pathname.split('/').filter(Boolean).at(-1));
  function event(name) { RP.api('/trips/'+id+'/events',{event:name,segment:index}).catch(()=>{}); }
  function selectSegment(selected) {
    index=selected;
    history.replaceState(null,'',RP.shareUrl(location.href,id,index));
    $('segment-select').value=String(index);
    const segment=trip.result.segments[index],a=trip.places[segment.from_index],b=trip.places[segment.to_index];
    $('nav-title').textContent=`${a.name} → ${b.name}`;
    const nav=new Navigation.TencentMapAdapter(config.tencent_nav_key).buildSegment(points,index);
    $('navigate').hidden=!nav.appUrl;
    if(nav.appUrl) $('navigate').href=nav.appUrl;
    $('nav-status').textContent=nav.reason;
    document.querySelectorAll('.segment').forEach((node,i)=>{
      node.classList.toggle('selected',i===index);
      node.querySelector('button').textContent=i===index?'当前路段':'选择这一段';
    });
  }
  async function load() {
    RP.clearError();$('reload').hidden=true;$('loading').hidden=false;
    try {
      if(!/^[a-zA-Z0-9-]+$/.test(id)) throw Error('行程链接无效');
      [trip,config]=await Promise.all([RP.api('/trips/'+id),RP.modeBanner()]);
      if(trip.status!=='optimized') {
        if(RP.token(id)) return location.replace('/confirm?trip_id='+id);
        throw Error('这份行程还没有生成结果，请让创建者完成地点确认和路线计算。');
      }
      const result=trip.result;
      index=RP.segmentIndex(location.href,result.segments.length);
      points=result.optimized.order.map(i=>trip.places[i]);
      if(result.source==='historical_demo') {$('mode-banner').hidden=false;$('mode-banner').textContent='历史样本演示 · 2026 年 9 月 14 日数据，非实时路况';}
      $('objective-label').textContent=result.objective==='fastest'?'按预计驾驶时间，选出更省时的访问顺序。':'按行驶里程，选出更少绕路的访问顺序。';
      $('route-order').textContent=points.map(p=>p.name).join(' → ');
      $('original-order').textContent=result.original.order.map(i=>trip.places[i].name).join(' → ');
      $('duration').textContent=RP.duration(result.optimized.total_duration);
      $('distance').textContent=RP.distance(result.optimized.total_distance);
      $('time-saving').textContent=RP.savingsText(result.savings.duration,'time');
      $('distance-saving').textContent=RP.savingsText(result.savings.distance,'distance');
      const snapshot=result.matrix;
      $('source').textContent=`${result.source==='historical_demo'?'腾讯历史样本':'腾讯地图'} · 分批查询（非同一时刻）\n${new Date(snapshot.started_at).toLocaleString('zh-CN')} — ${new Date(snapshot.finished_at).toLocaleString('zh-CN')}\n比较了 ${result.candidates_evaluated} 种访问顺序。`;
      $('trip-id').textContent=`行程 ${trip.trip_id} · 已保存，可通过链接再次打开。`;
      $('segments').replaceChildren();$('segment-select').replaceChildren();
      result.segments.forEach((s,i)=>{
        const a=trip.places[s.from_index],b=trip.places[s.to_index],row=el('div',undefined,'segment');
        row.append(el('div',`${i+1}. ${a.name} → ${b.name}`,'segment-line'),el('div',`${RP.distance(s.distance_m)} · 约 ${RP.duration(s.duration_s)}`,'small'));
        const button=el('button',i===index?'当前路段':'选择这一段');button.type='button';button.addEventListener('click',()=>{selectSegment(i);$('navigation').scrollIntoView({behavior:'smooth'});});
        row.append(button);$('segments').append(row);
        const option=el('option',`第 ${i+1} 段 · 到 ${b.name}`);option.value=String(i);$('segment-select').append(option);
      });
      $('result').hidden=false;selectSegment(index);
      RouteMap.render(trip,config.tencent_js_key);
    } catch(e){RP.error(e);$('reload').hidden=false;} finally{$('loading').hidden=true;}
  }
  $('segment-select').addEventListener('change',()=>selectSegment(Number($('segment-select').value)));
  $('navigate').addEventListener('click',()=>{event('navigation_click');$('nav-status').textContent='已尝试打开腾讯地图。若没有响应，请在系统浏览器打开或复制目的地。';});
  $('copy-destination').addEventListener('click',()=>{
    const p=points[index+1];RP.copy(`${p.name}\n${p.address}\n纬度 ${p.lat}，经度 ${p.lng}（GCJ-02）`);
  });
  $('share').addEventListener('click',()=>{RP.copy(RP.shareUrl(location.href,id,index));event('share_click');});
  $('reload').addEventListener('click',()=>location.reload());
  load();
})();
