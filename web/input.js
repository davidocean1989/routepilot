'use strict';
(() => {
  const {$,el}=RP;
  let locations=[{query:'',city:''},{query:'',city:''},{query:'',city:''}];
  RP.modeBanner().catch(RP.error);
  function render() {
    $('waypoints').replaceChildren();
    locations.forEach((p,i)=>{
      const wrapper=el('div',undefined,'location-row');
      wrapper.append(el('div',`第 ${i+1} 站`,'field-label'));
      const row=el('div',undefined,'row');
      for (const [field,placeholder] of [['query','地点名称或地址'],['city','城市（可选）']]) {
        const input=el('input'); input.value=p[field]; input.placeholder=placeholder;
        input.setAttribute('aria-label',`第 ${i+1} 站${field==='query'?'地点':'城市'}`);
        input.maxLength=field==='query'?200:100; input.required=field==='query';
        input.addEventListener('input',()=>{p[field]=input.value;}); row.append(input);
      }
      wrapper.append(row);
      const controls=el('div',undefined,'waypoint-controls');
      for (const [label,move] of [['上移',-1],['下移',1],['删除',0]]) {
        const b=el('button',label); b.type='button'; b.setAttribute('aria-label',`${label}第 ${i+1} 站`);
        b.disabled=move===0 ? locations.length<=3 : i+move<0 || i+move>=locations.length;
        b.addEventListener('click',()=>{ if(move) [locations[i],locations[i+move]]=[locations[i+move],locations[i]]; else locations.splice(i,1); render(); });
        controls.append(b);
      }
      wrapper.append(controls); $('waypoints').append(wrapper);
    });
    $('count').textContent=`${locations.length} 站`; $('add').disabled=locations.length>=8;
  }
  function fill(data) {
    locations=data.waypoints.map(p=>({...p}));
    $('start').value=data.start.query; $('start-city').value=data.start.city||'';
    $('end').value=data.end?.query||''; $('end-city').value=data.end?.city||'';
    $('end-mode').value=data.end_mode; $('objective').value=data.objective;
    $('sentence').value=data.raw_input||''; setEnd(); render();
  }
  function setEnd() { const fixed=$('end-mode').value==='fixed'; $('end-fields').hidden=!fixed; $('end').required=fixed; }
  $('end-mode').addEventListener('change',setEnd);
  $('add').addEventListener('click',()=>{if(locations.length<8) {locations.push({query:'',city:''});render();}});
  $('parse').addEventListener('click',()=>{
    RP.clearError(); const data=RP.parseSentence($('sentence').value);
    if(!data) return RP.error(Error('这句话暂时无法完整拆分，请直接填写下方地点，或参考示例句式。'));
    fill(data);
  });
  $('example').addEventListener('click',()=>{RP.clearError();fill(RP.parseSentence('从杭州出发，想去乌镇、西塘古镇、南浔古镇，最后到上海'));});
  try { const draft=sessionStorage.getItem('input-draft'); if(draft) fill(JSON.parse(draft)); else render(); } catch { render(); }
  $('trip-form').addEventListener('submit',async event=>{
    event.preventDefault(); RP.clearError();
    const data={start:{query:$('start').value.trim(),city:$('start-city').value.trim()}, waypoints:locations.map(p=>({query:p.query.trim(),city:p.city.trim()})),
      end_mode:$('end-mode').value, end:$('end-mode').value==='fixed'?{query:$('end').value.trim(),city:$('end-city').value.trim()}:null,
      objective:$('objective').value,raw_input:$('sentence').value};
    $('submit').disabled=true; $('loading').hidden=false;
    try {
      RP.store('input-draft',JSON.stringify(data));
      const result=await RP.api('/trips',data);
      RP.store('edit:'+result.trip.trip_id,result.edit_token);
      location.assign('/confirm?trip_id='+encodeURIComponent(result.trip.trip_id));
    } catch(e){RP.error(e);$('submit').disabled=false;$('loading').hidden=true;}
  });
})();
