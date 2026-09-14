const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(__dirname+'/../dist/spike04.html','utf8');
function node(){return {value:'',hidden:false,events:{},children:[],addEventListener(k,f){this.events[k]=f},appendChild(n){this.children.push(n)},removeAttribute(k){delete this[k]},setAttribute(k,v){this[k]=v}}}
const nodes=Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(x=>[x[1],node()]));
nodes.provider.value='tencent';nodes.path04.value='当前段 App';nodes.outcome04.value='未测试';
const document={visibilityState:'visible',events:{},getElementById:id=>nodes[id],createElement:node,addEventListener(k,f){this.events[k]=f}};
const ctx={document,URL,URLSearchParams,location:{href:'https://example.test/spike04?trip_id=rp-spike04-demo-v1&segment=2'},history:{replaceState(){}},navigator:{userAgent:'iPhone Safari'},localStorage:{getItem(){return null},setItem(){}},setTimeout(){},clearTimeout(){}};
vm.createContext(ctx);for(const f of ['navigation04.js','spike04.js'])vm.runInContext(fs.readFileSync(__dirname+'/../dist/'+f,'utf8'),ctx);
assert.equal(nodes.provider.value,'amap','Default must follow the tested recommended map');
for(const [id,scheme,label] of [['amap','iosamap:','高德地图'],['tencent','qqmap:','腾讯地图'],['baidu','baidumap:','百度地图'],['amap','iosamap:','高德地图']]){
 nodes.provider.value=id;nodes.provider.events.change();
 assert.equal(new URL(nodes.start.href).protocol,scheme);assert.ok(nodes.start.textContent.includes(label));
 assert.equal(nodes.full.hidden,id!=='amap');assert.equal(nodes['web-test'].open,id!=='baidu');
 assert.equal(new URL(nodes['share-text'].value).searchParams.get('provider'),id);
 if(id==='tencent')assert.match(nodes['web-note'].textContent,/丢失/);
 if(id==='baidu')assert.match(nodes['web-note'].textContent,/周边/);
}
console.log('PASS: full page map switching, correct schemes and labels, full-route eligibility, failed-web demotion and share-map persistence (DOM harness, not phone).');
