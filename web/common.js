'use strict';
globalThis.RP = (() => {
  const $ = id => document.getElementById(id);
  function parseSentence(value) {
    const text = value.trim();
    const match = text.match(/^(?:我)?(?:今天|明天)?从(.+?)(?:出发)?[，,]\s*(?:想去|要去|去)(.+?)[，,]\s*(?:最后到|最后去|终点是|晚上到|晚上住)(.+?)[。！!？?]?$/);
    if (!match) return null;
    const queries = match[2].split(/[、；;]/).map(x => x.trim());
    if (queries.length < 3 || queries.length > 8 || queries.some(x => !x)) return null;
    return {start: {query: match[1].trim(), city: ''}, waypoints: queries.map(query => ({query, city:''})),
      end: {query: match[3].trim(), city:''}, end_mode:'fixed', objective:'fastest', raw_input:text};
  }
  function shareUrl(href, id, segment) {
    if (!/^[a-zA-Z0-9-]+$/.test(id) || !Number.isInteger(segment) || segment < 0) throw Error('分享参数无效');
    const url = new URL('/t/'+encodeURIComponent(id), href);
    url.searchParams.set('segment', String(segment));
    return url.href;
  }
  function segmentIndex(href, count) {
    const p = new URL(href).searchParams, value = p.get('segment') ?? '0';
    if (p.getAll('segment').length > 1 || !/^\d+$/.test(value) || Number(value) >= count) throw Error('路段链接无效，请打开原行程链接。');
    return Number(value);
  }
  function duration(seconds) {
    const minutes = Math.round(Math.abs(seconds) / 60);
    return minutes >= 60 ? `${Math.floor(minutes/60)} 小时 ${minutes%60} 分` : `${minutes} 分钟`;
  }
  const distance = meters => (Math.abs(meters)/1000).toFixed(1)+' 公里';
  function savingsText(value, kind) {
    if (value === 0) return kind === 'time' ? '驾驶时间相同' : '行驶距离相同';
    return (value > 0 ? '节省 ' : '增加 ') + (kind === 'time' ? duration(value) : distance(value));
  }
  async function api(path, body, token) {
    const headers = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (token) headers['X-Trip-Token'] = token;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 195000);
    try {
      const r = await fetch('/api'+path, {method:body === undefined ? 'GET':'POST', headers,
        body:body === undefined ? undefined:JSON.stringify(body), signal:controller.signal});
      const data = await r.json();
      if (!r.ok) {
        const error = new Error(data.error?.message || '请求失败，请重试。');
        error.code = data.error?.code;
        error.requestId = data.error?.request_id;
        throw error;
      }
      return data;
    } catch (e) {
      if (e.name === 'AbortError') throw Error('等待时间较长，请刷新检查行程状态后重试。');
      throw e;
    } finally { clearTimeout(timer); }
  }
  function error(e) {
    const box = $('error');
    box.textContent = (e.message || '连接失败，请稍后重试。') + (e.requestId ? `（请求编号 ${e.requestId}）`: '');
    box.hidden = false;
    box.focus();
  }
  function clearError() { $('error').hidden = true; }
  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function token(id) {
    try { return sessionStorage.getItem('edit:'+id) || ''; } catch { return ''; }
  }
  function store(key, value) {
    try { sessionStorage.setItem(key, value); }
    catch { throw Error('浏览器暂时不能保存行程编辑状态，请允许网站存储或换一个浏览器。'); }
  }
  async function copy(text) {
    try { await navigator.clipboard.writeText(text); $('copy-status').textContent = '已复制'; }
    catch {
      const box = $('copy-fallback'); box.value = text; box.hidden = false; box.focus(); box.select();
      $('copy-status').textContent = '请长按或选中文本复制';
    }
  }
  async function modeBanner() {
    const config = await api('/config');
    const banner = $('mode-banner');
    if (config.map_mode === 'demo') {
      banner.hidden = false;
      banner.textContent = '历史样本演示 · 2026 年 9 月 14 日数据，非实时路况';
    }
    return config;
  }
  return {$, parseSentence, shareUrl, segmentIndex, duration, distance, savingsText,
    api, error, clearError, el, token, store, copy, modeBanner};
})();
