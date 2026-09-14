'use strict';
const TENCENT_CLIENT_KEY='YOUR_TENCENT_MAP_KEY';
(()=>{
 const $=id=>document.getElementById(id),n=Navigation04,t=n.trip;let share;
 try{share=n.parseShare(location.href);}catch(e){$('error').textContent=e.message;$('surface').hidden=true;return;}
 const wechat=/MicroMessenger/i.test(navigator.userAgent);$('os').value=/Android/i.test(navigator.userAgent)?'android':'ios';
 $('environment').textContent=wechat?'微信内打开：若无法唤起，请在系统浏览器重试。':'普通浏览器：请在手机上测试 App 接收结果。';
 $('trip-label').textContent=`行程编号：${t.trip_id} · 版本 ${t.revision}`;
 t.points.forEach((p,i)=>{const li=document.createElement('li');li.textContent=`${p.name}（${p.lat}, ${p.lng}；GCJ-02）`;$('all-stops').appendChild(li);if(i<4){const o=document.createElement('option');o.value=i;o.textContent=`第 ${i+1} 段：${p.name} → ${t.points[i+1].name}`;$('segment').appendChild(o);}});
 $('segment').value=String(share.segment);$('provider').value=share.provider;const storeKey='routepilot-spike04-records-v1';let records=[];
 try{const v=JSON.parse(localStorage.getItem(storeKey)||'[]');if(Array.isArray(v))records=v;}catch{}
 function render(){const index=Number($('segment').value);const a=n.adapter($('provider').value,$('os').value,TENCENT_CLIENT_KEY);const leg=a.buildSegment(t,index),full=a.buildFullRoute(t);$('start').href=leg.appUrl;$('web').href=leg.webUrl;
  const provider=$('provider').value,label={amap:'高德地图',tencent:'腾讯地图',baidu:'百度地图'}[provider];
  $('start').textContent=`打开${label} · 当前段 ↗`;$('web').textContent=`查看${label}网页路线 ↗`;$('full').textContent=`用${label}接收完整行程 ↗`;
  $('web-test').open=provider!=='baidu';$('web-summary').textContent=provider==='baidu'?'百度网页故障复测（非推荐入口）':'网页路线入口';
  $('web-note').textContent={amap:'本轮用户反馈：网页路线和网页内打开高德 App 均能带入起终点。',tencent:'网页可查看路线，但用户反馈网页内二次跳 App/小程序会丢失起终点。需要 App 时，请使用本页上方直达按钮。',baidu:'本轮网页落在“周边”页，未显示路线。原因尚未定位，原链接仅保留作复测；优先使用本页直达百度 App，或复制目的地。'}[provider];
  $('map-advice').textContent={amap:'优先测试：用户已反馈完整行程地点全部带入。请继续核对顺序与实际导航启动；最大途经点数量仍未知。',tencent:'单段起终点已通过用户实测；完整多途经点协议尚未确认，因此不提供整条路线按钮。',baidu:'单段起终点已通过用户实测。iOS 多途经点参数尚未确认，因此只提供逐段入口；Android 仍可进行完整路线实验。'}[provider];$('segment-detail').textContent=`本段传入 ${t.points[index].name} → ${t.points[index+1].name}`;
  $('full').hidden=!full.appUrl;if(full.appUrl)$('full').href=full.appUrl;else $('full').removeAttribute('href');$('full-note').textContent=full.appUrl?(provider==='amap'?'用户已反馈本例全部3个途经点带入；请继续核对顺序及导航启动，不代表已验证最大容量。':'按官方参数构造的实验入口，仍待此平台真机验证。'):full.reason;
  $('share-text').value=n.shareUrl(location.href,t.trip_id,index,provider);history.replaceState(null,'',$('share-text').value);$('saved').textContent=`本浏览器已有 ${records.length} 条记录`;
 }
 for(const id of ['provider','os','segment'])$(id).addEventListener('change',()=>{render();$('outcome04').value='未测试';$('status').textContent='已更换测试组合，请重新点击并核对结果。';});
 let attempted=false,left=false,timer;
 for(const id of ['start','full','web'])$(id).addEventListener('click',()=>{attempted=true;left=false;clearTimeout(timer);$('path04').value=id==='full'?'整条路线 App':id==='web'?'当前段网页':'当前段 App';$('status').textContent=`已请求${{amap:'高德地图',tencent:'腾讯地图',baidu:'百度地图'}[$('provider').value]}。请核对打开的 App 名称、实际接收的地点和顺序。`;timer=setTimeout(()=>{if(!left)$('status').textContent='暂未确认打开。可在系统浏览器重试，或使用网页地图、复制目的地。';},2200);});
 document.addEventListener('visibilitychange',()=>{if(!attempted)return;if(document.visibilityState==='hidden'){left=true;clearTimeout(timer);}else if(left)$('status').textContent='已返回行程。请记录实际结果，再自行选择下一段；不会自动标记到达。';});
 async function copy(s){$('copy04').value=s;try{await navigator.clipboard.writeText(s);$('copy04').hidden=true;$('saved').textContent='已复制，可自行粘贴回对话。';}catch{$('copy04').hidden=false;$('copy04').focus();$('copy04').select();$('saved').textContent='请长按下方文字全选并复制。';}}
 $('share').addEventListener('click',()=>copy($('share-text').value));$('place').addEventListener('click',()=>{const p=t.points[Number($('segment').value)+1];copy(`${p.name}\nGCJ-02 纬度,经度：${p.lat},${p.lng}`);});
 $('record').addEventListener('click',()=>{const r={build:'spike04-v2',timestamp:new Date().toISOString(),trip_id:t.trip_id,revision:t.revision,segment:Number($('segment').value),provider:$('provider').value,os:$('os').value,browser:wechat?'wechat':'external',userAgent:navigator.userAgent,device:$('device04').value,path:$('path04').value,outcome:$('outcome04').value,notes:$('notes04').value};records.push(r);try{localStorage.setItem(storeKey,JSON.stringify(records));$('saved').textContent=`已保存 ${records.length} 条记录到本机`;}catch{$('saved').textContent='浏览器无法保存，请立即复制全部记录。';}});
 $('export').addEventListener('click',()=>copy(JSON.stringify({build:'spike04-v2',records},null,2)));render();
})();
