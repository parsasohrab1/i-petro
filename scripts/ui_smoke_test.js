const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('platform/index.html', 'utf8');
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
let code = blocks[0];
// stop the IIFE before boot() runs, but expose the internals for testing
const endMark = 'boot();\n})();';
if (!code.includes(endMark)) { console.error('boot marker not found'); process.exit(1); }
code = code.replace(endMark, 'window.__T = {S, VIEWS, poolItems, fuMark, poolTake, fuNextForm, fuMailView, fuPill, poolTaken, fuOf};\n})();');
const sandbox = { console, document: { documentElement: { lang: '', dir: '' }, addEventListener: () => {}, querySelectorAll: () => [], querySelector: () => null, getElementById: () => null, createElement: () => ({ style: {}, click: () => {} }) }, localStorage: { getItem: () => null, setItem: () => {} }, location: { href: '' }, navigator: { clipboard: { writeText: async () => {} } }, URL: { createObjectURL: () => '' }, Blob: function () {}, setInterval: () => {}, setTimeout: () => {}, fetch: async () => ({ ok: false, json: async () => ({}) }), FormData: function () {}, XMLHttpRequest: function () {}, alert: () => {}, confirm: () => true, prompt: () => null };
sandbox.window = sandbox;
sandbox.MutationObserver = function () { return { observe: () => {} }; };
sandbox.matchMedia = () => ({ matches: false, addEventListener: () => {} });
const ctx = vm.createContext(sandbox);
try {
  vm.runInContext(code, ctx);
} catch (e) { console.error('LOAD FAIL:', e.message); process.exit(1); }
const T = sandbox.window.__T;
if (!T) { console.error('no exports'); process.exit(1); }
const { S, VIEWS, poolItems } = T;
S.m.requests = [
  { id: 'req-a', investor: 'Aramco Ventures', investor_id: 'aramco-ventures', country: 'Saudi Arabia', product: 'i-drill', status: 'not sent', notes: 'drilling analytics fits', channel: 'https://aramcoventures.com/contact/' },
  { id: 'req-b', investor: 'Qatar Development Bank', investor_id: 'qatar-development-bank', country: 'Qatar', product: 'inno-medical-telecare', status: 'taken', taken_by: 'u1', taken_by_name: 'Narges', taken_at: '2026-11-10T10:00:00Z', fu: { email: { done: true, at: '2026-11-10T09:00:00Z', by: 'u1' }, deck: { done: true, at: '2026-11-10T09:30:00Z' }, meeting: {}, next: { text: 'send follow-up', date: '2026-11-20' } } }
];
S.m.pool = [{ id: 'p1', title: 'Demo OGIM amadesagi', investor: 'Test Investor', product: 'OGIM---NISOC', desc: 'amadesagi', priority: 'high', due: '2026-11-15' }];
S.members = [{ id: 'u1', full_name: 'Narges' }, { id: 'u2', full_name: 'Parsa' }];
S.tasks = [{ id: 'outreach_req-a', title: 'Tamase ba Aramco', assignee: 'u1', assignee_name: 'Narges', due: '2026-11-13', status: 'todo', updated: '2026-11-10T10:00:00Z', pool_ref: 'req-a' }];
S.invMail = { 'aramco-ventures': { subject: 'i-drill - AI product matched', body: 'Dear ...', attachment: 'i-drill.pptx', to: '' } };
S.outlook = { connected: false };
S.mod = 'market'; S.sub = 'taskpool'; S.q = ''; S.me = { id: 'u1', isOwner: true };
let ok = true;
try {
  const tp = VIEWS['market.taskpool']();
  console.log('taskpool: length', tp.length, '| banner:', tp.includes('قاعده‌ی این بخش'), '| take btn:', tp.includes('برای انجام برمی‌دارم'), '| assign btn:', tp.includes('تعریف برای شخص دیگر'), '| taken section:', tp.includes('برداشته‌شده یا واگذارشده'));
  const items = poolItems();
  console.log('pool items:', items.length, '(expect 2: req-a + custom p1)');
  S.sub = 'followup';
  const fu = VIEWS['market.followup']();
  console.log('followup: length', fu.length, '| outlook card:', fu.includes('اتصال Outlook'), '| step1:', fu.includes('۱. ارسال ایمیل برای سرمایه‌گذار'), '| step2:', fu.includes('۲. ارسال پیچ دک برای سرمایه‌گذار'), '| step3:', fu.includes('۳. ارائه آنلاین یا جلسه آنلاین'), '| step4:', fu.includes('۴. اقدام بعدی'), '| draft btn:', fu.includes('نمایش درفت'));
  // fuPill rendering
  const rb = S.m.requests[1];
  const pillDone = T.fuPill(rb, 'email'), pillNext = T.fuPill(rb, 'next'), pillMeet = T.fuPill(rb, 'meeting');
  console.log('fuPill email done:', pillDone.includes('p-ok'), '| next with date:', pillNext.includes('۱۴۰۴') || pillNext.includes('2026') || pillNext.length > 0, '| meeting open:', pillMeet.includes('p-warn'));
  // SUBS wiring
  const subs = VIEWS['market.investors'] ? Object.keys(VIEWS).filter(k => k.startsWith('market.')) : [];
  console.log('market views:', subs.join(', '));
} catch (e) { console.error('RENDER FAIL:', e.message, e.stack.split('\n')[1] || ''); ok = false; }
process.exit(ok ? 0 : 1);
