'use strict';
globalThis.Navigation = (() => {
  const unavailable = reason => ({appUrl:null, reason, navigationConfirmed:false});
  function pair(points, index) {
    if (!Array.isArray(points) || !Number.isInteger(index) || index < 0 || index >= points.length-1) throw Error('没有这个路段');
    const selected = points.slice(index, index+2);
    for (const p of selected) {
      if (typeof p.name !== 'string' || !p.name.trim() || p.coordinate_system !== 'GCJ-02' ||
          !Number.isFinite(p.lat) || !Number.isFinite(p.lng) || Math.abs(p.lat)>90 || Math.abs(p.lng)>180) throw Error('地点坐标无效');
    }
    return selected;
  }
  class NavigationAdapter {
    capabilities() { return {segment:false, fullRoute:false, deviceVerified:false}; }
    buildSegment(points, index) { pair(points,index); return unavailable('此地图导航尚未启用，可复制目的地后打开地图。'); }
    buildFullRoute() { return unavailable('请逐段导航，完整行程会保留在本页。'); }
  }
  class TencentMapAdapter extends NavigationAdapter {
    constructor(key) { super(); this.key = key; }
    capabilities() { return {...super.capabilities(), segment:!!this.key}; }
    buildSegment(points, index) {
      const [a,b] = pair(points,index);
      if (!this.key) return unavailable('腾讯导航暂未配置，先复制目的地到地图 App。');
      const params = new URLSearchParams({type:'drive', from:a.name, fromcoord:`${a.lat},${a.lng}`,
        to:b.name, tocoord:`${b.lat},${b.lng}`, referer:this.key});
      return {appUrl:'qqmap://map/routeplan?'+params, reason:'请在地图中核对起终点并开始导航。', navigationConfirmed:false};
    }
  }
  class BaiduMapAdapter extends NavigationAdapter {}
  class AmapAdapter extends NavigationAdapter {}
  function adapter(provider,key) {
    if (provider==='tencent') return new TencentMapAdapter(key);
    if (provider==='baidu') return new BaiduMapAdapter();
    if (provider==='amap') return new AmapAdapter();
    throw Error('未知地图');
  }
  return {NavigationAdapter, TencentMapAdapter, BaiduMapAdapter, AmapAdapter, adapter};
})();
