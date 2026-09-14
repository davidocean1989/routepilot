/* Disposable Spike 04 protocol probe. No real-device capability is implied. */
'use strict';
globalThis.Navigation04=(()=>{
 const points=[
  {name:'杭州东站',lat:30.291331,lng:120.212998},
  {name:'乌镇西栅景区1号停车场-入口',lat:30.745906,lng:120.48884},
  {name:'南浔古镇1号停车场-入口',lat:30.869188,lng:120.430771},
  {name:'西塘古镇景区第一地上停车场',lat:30.93898,lng:120.888689},
  {name:'上海虹桥站',lat:31.194106,lng:121.320666}
 ];
 const trip={trip_id:'rp-spike04-demo-v1',revision:1,coordinateSystem:'gcj02',points};
 const url=(base,params)=>base+'?'+new URLSearchParams(params);
 const ll=p=>`${p.lat},${p.lng}`;
 const named=p=>`name:${p.name}|latlng:${ll(p)}`;
 const unsupported=reason=>({appUrl:null,productionEnabled:false,reason});
 class NavigationAdapter {
  constructor(os){if(!['ios','android'].includes(os))throw Error('请选择 iOS 或 Android');this.os=os;}
  buildSegment(t,index){if(!Number.isInteger(index)||index<0||index>=t.points.length-1)throw Error('路段不存在');return this.build(t.points.slice(index,index+2));}
  buildFullRoute(){return unsupported('当前协议没有确认完整多站交付；请按段导航。');}
  capabilities(){return {fullRoute:'unknown',maxWaypoints:null,orderVerified:false,universalLinkVerified:false};}
  result(appUrl,webUrl,count){return {appUrl,webUrl,pointCount:count,navigationConfirmed:false,productionEnabled:false};}
 }
 class TencentMapAdapter extends NavigationAdapter {
  constructor(os,key){super(os);this.key=key;}
  build(p){if(!this.key)throw Error('腾讯地图测试需要客户端 Key');const a=p[0],b=p.at(-1);const data={type:'drive',from:a.name,fromcoord:ll(a),to:b.name,tocoord:ll(b)};return this.result(url('qqmap://map/routeplan',{...data,referer:this.key}),url('https://apis.map.qq.com/uri/v1/routeplan',{...data,coord_type:'2',policy:'0',referer:'RoutePilot'}),2);}
 }
 class BaiduMapAdapter extends NavigationAdapter {
  build(p){const data={origin:named(p[0]),destination:named(p.at(-1)),coord_type:'gcj02',mode:'driving'};
   const app={...data,src:`${this.os==='ios'?'ios':'andr'}.routepilot.spike04`};
   if(p.length>2)app.viaPoints=JSON.stringify({viaPoints:p.slice(1,-1).map(({name,lat,lng})=>({name,lat,lng}))});
   return this.result(url(this.os==='ios'?'baidumap://map/direction':'bdapp://map/direction',app),p.length===2?url('https://api.map.baidu.com/direction',{...data,output:'html',src:'webapp.routepilot.spike04'}):null,p.length);
  }
  capabilities(){return {...super.capabilities(),fullRoute:this.os==='android'?'documented-unverified':'unknown'};}
  buildFullRoute(t){return this.os==='android'?this.build(t.points):unsupported('百度 iOS 文档未确认多途经点参数，使用按段导航。');}
 }
 class AmapAdapter extends NavigationAdapter {
  build(p){const a=p[0],b=p.at(-1);const data={sourceApplication:'RoutePilot',slat:a.lat,slon:a.lng,sname:a.name,dlat:b.lat,dlon:b.lng,dname:b.name,dev:'0',t:'0',m:'0'};
   if(p.length>2){const via=p.slice(1,-1);data.vian=via.length;data.vialons=via.map(x=>x.lng).join('|');data.vialats=via.map(x=>x.lat).join('|');data.vianames=via.map(x=>x.name).join('|');}
   return this.result(url(this.os==='ios'?'iosamap://path':'amapuri://route/plan/',data),p.length===2?url('https://uri.amap.com/navigation',{from:`${a.lng},${a.lat},${a.name}`,to:`${b.lng},${b.lat},${b.name}`,mode:'car',src:'RoutePilot',callnative:'0'}):null,p.length);
  }
  capabilities(){return {...super.capabilities(),fullRoute:'documented-unverified'};}
  buildFullRoute(t){return this.build(t.points);}
 }
 function adapter(id,os,key){if(id==='tencent')return new TencentMapAdapter(os,key);if(id==='baidu')return new BaiduMapAdapter(os);if(id==='amap')return new AmapAdapter(os);throw Error('未知地图');}
 function parseShare(href){const p=new URL(href).searchParams;const id=p.get('trip_id')??trip.trip_id;const s=p.get('segment')??'0';if(p.getAll('trip_id').length>1||id!==trip.trip_id)throw Error('行程不存在：本原型只提供固定测试行程。');if(!/^[0-3]$/.test(s)||p.getAll('segment').length>1)throw Error('路段参数无效');const provider=p.get('provider')??'amap';if(!['amap','tencent','baidu'].includes(provider)||p.getAll('provider').length>1)throw Error('地图参数无效');return {trip_id:id,segment:Number(s),provider};}
 function shareUrl(href,id,segment,provider='amap'){const u=new URL(href);u.search='';u.hash='';u.searchParams.set('trip_id',id);u.searchParams.set('segment',String(segment));u.searchParams.set('provider',provider);parseShare(u.href);return u.href;}
 return {trip,adapter,parseShare,shareUrl,NavigationAdapter,TencentMapAdapter,BaiduMapAdapter,AmapAdapter};
})();
