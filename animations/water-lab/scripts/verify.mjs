// Headless Chrome (CDP) 验证脚本。
// 先启动：chrome --headless=new --remote-debugging-port=9222
// 用法：node scripts/verify.mjs [cdpPort]
// 步骤：打开演示页 → 等真实时间 3.2s → 收集 JS 异常/console.error → 读取状态栏与画布蓝像素。

const CDP_PORT = process.argv[2] || 9222;
const pageUrl = 'http://127.0.0.1:8123/index.html';
const httpBase = 'http://127.0.0.1:' + CDP_PORT;

function httpJson(path) {
  return fetch(httpBase + path).then((r) => r.json());
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function cdp(ws, id, method, params) {
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve) => {
    const t = setTimeout(() => resolve({ timeout: true }), 8000);
    ws.addEventListener('message', function h(ev) {
      const m = JSON.parse(ev.data);
      if (m.id === id) { clearTimeout(t); ws.removeEventListener('message', h); resolve(m); }
    });
  });
}

// 复用启动时已加载 pageUrl 的标签页。
const tabs = await httpJson('/json/list');
const tab = tabs.find((t) => t.type === 'page' && t.url.includes('/index.html')) || tabs.find((t) => t.type === 'page');
if (!tab) { console.error('未找到页面标签页'); process.exit(1); }
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
await cdp(ws, 1, 'Runtime.enable', {});
await cdp(ws, 2, 'Page.enable', {});

const errors = [];
ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.method === 'Runtime.exceptionThrown') {
    errors.push('EXCEPTION: ' + (m.params.exceptionDetails.text || ''));
  } else if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
    errors.push('CONSOLE: ' + m.params.args.map((a) => a.value || a.description || '').join(' '));
  }
});

await sleep(3200);

const expr = [
  '(function(){',
  " const status = (document.getElementById('status')||{}).textContent || '';",
  " const cv = document.getElementById('scene');",
  ' let pixels = null;',
  ' if (cv) {',
  "  const c = document.createElement('canvas'); c.width = cv.width; c.height = cv.height;",
  "  const g = c.getContext('2d');",
  "  try { g.drawImage(cv,0,0); } catch(e){ return JSON.stringify({status, drawError:String(e)}); }",
  '  const d = g.getImageData(0,0,c.width,c.height).data;',
  '  let blue=0, nonBg=0; const n=d.length/4;',
  '  for (let i=0;i<n;i++){',
  '   const r=d[i*4], gv=d[i*4+1], b=d[i*4+2];',
  '   if (b>150 && b>r+40 && b>gv+20) blue++;',
  '   if (!(r>230&&gv>230&&b>230)) nonBg++;',
  '  }',
  '  pixels = { bluePx: blue, nonBgPx: nonBg, totalPx: n };',
  ' }',
  " return JSON.stringify({ status, pixels });",
  '})()',
].join('\n');

const res = await cdp(ws, 10, 'Runtime.evaluate', { expression: expr, returnByValue: true });
let info = { status: '', pixels: null };
try { info = JSON.parse(res.result && res.result.result && res.result.result.value); }
catch (e) { info = { raw: res.result && res.result.result && res.result.result.value, err: String(e) }; }

console.log('STATUS_TEXT:', info.status);
if (info.pixels) {
  const p = info.pixels;
  console.log('PIXELS: blue=%d nonBg=%d total=%d  (waterRatio=%.3f)',
    p.bluePx, p.nonBgPx, p.totalPx, p.bluePx / p.totalPx);
}
if (info.raw) console.log('RAW:', info.raw);
console.log('JS_ERRORS:', errors.length === 0 ? 'none' : errors.join(' | '));

ws.close();
process.exit(0);