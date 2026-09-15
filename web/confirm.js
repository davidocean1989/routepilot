'use strict';
(() => {
  const {$,el}=RP;
  let trip,id,token;
  async function load() {
    RP.clearError(); $('retry').hidden=true; $('loading').hidden=false; $('confirm-form').hidden=true;
    try {
      const p=new URL(location.href).searchParams; id=p.get('trip_id');
      if(!id || p.getAll('trip_id').length!==1) throw Error('行程链接无效，请返回输入页。');
      token=RP.token(id); trip=await RP.api('/trips/'+encodeURIComponent(id));
      if(trip.status==='optimized') return location.replace('/t/'+id);
      if(!token) throw Error('此浏览器只能查看，请回到创建行程的浏览器继续，或重新输入。');
      if(trip.status==='draft') trip=await RP.api('/trips/'+id+'/resolve',{revision:trip.revision},token);
      $('candidates').replaceChildren();
      $('confirmed-note').hidden=trip.status!=='confirmed';
      if(trip.status==='confirmed') {
        trip.places.forEach((p,i)=>$('candidates').append(el('p',`${i+1}. ${p.name} · ${p.address}`)));
      } else trip.candidates.forEach((options,i)=>{
        const field=el('fieldset'), input=trip.input;
        const queries=[input.start,...input.waypoints,...(input.end?[input.end]:[])];
        const role=i===0?'起点':(input.end && i===queries.length-1?'终点':`途经点 ${i}`);
        field.append(el('legend',`${role} · ${queries[i].query}`));
        options.forEach(p=>{
          const label=el('label',undefined,'choice'), radio=el('input');
          radio.type='radio';radio.name='place-'+i;radio.value=p.candidate_id;radio.required=true;
          const description=el('span'),title=el('span',p.name),city=el('span',p.city,'city');
          title.append(city);description.append(title,el('span',p.address,'address'));label.append(radio,description);field.append(label);
        }); $('candidates').append(field);
      });
      $('confirm').textContent=trip.status==='confirmed'?'继续计算路线 →':'确认地点，帮我排路线 →';
      $('confirm').disabled=false; $('confirm-form').hidden=false;
    } catch(e) {RP.error(e);$('retry').hidden=false;} finally {$('loading').hidden=true;}
  }
  RP.modeBanner().catch(RP.error);
  $('retry').addEventListener('click',load);
  $('confirm-form').addEventListener('submit',async event=>{
    event.preventDefault();RP.clearError();$('confirm').disabled=true;$('loading').hidden=false;
    $('loading').textContent='正在比较各个访问顺序，地图繁忙时可能需要 1–3 分钟…';
    try {
      if(trip.status==='resolved') {
        const fields=new FormData($('confirm-form'));
        trip=await RP.api('/trips/'+id+'/confirm',{revision:trip.revision,candidate_ids:trip.candidates.map((_,i)=>fields.get('place-'+i))},token);
      }
      trip=await RP.api('/trips/'+id+'/optimize',{revision:trip.revision},token);
      location.assign('/t/'+id);
    } catch(e) {RP.error(e);$('retry').hidden=false;$('confirm-form').hidden=true;} finally {$('loading').hidden=true;}
  });
  load();
})();
