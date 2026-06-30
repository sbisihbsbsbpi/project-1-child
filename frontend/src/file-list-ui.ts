/*
  Simple file list UI that fetches from http://localhost:1234 and renders
  a filterable list separated by Frontend vs Backend.

  Expected backend response at GET http://localhost:1234/files:
    - either: string[]              (array of file paths)
    - or:    { files: string[] }    (object with files key)

  Usage in your app (temporary / debug):
    import './file-list-ui'; // auto-mounts a floating panel

  Or manual mount:
    import { mountFileListUI } from './file-list-ui';
    mountFileListUI();
*/

const API_BASE = 'http://localhost:1234';
const API_FILES = `${API_BASE}/files`;
const API_FILTERS = `${API_BASE}/filters`;

type FilesResponse = { files: string[]; total?: number; offset?: number; limit?: number };
type FiltersResponse = { scopes: string[]; extensions: string[] };

function computeExt(path: string): string {
  const base = path.split('/').pop() || '';
  const idx = base.lastIndexOf('.');
  return idx > 0 ? base.slice(idx).toLowerCase() : '';
}

function scopeOf(path: string): 'frontend' | 'backend' | 'other' {
  const p = path.replace(/^\.\/?/, '');
  if (p.startsWith('frontend/') || p.includes('/frontend/')) return 'frontend';
  if (p.startsWith('backend/') || p.includes('/backend/')) return 'backend';
  return 'other';
}

async function fetchFilters(): Promise<FiltersResponse> {
  const r = await fetch(API_FILTERS, { cache: 'no-store' });
  if (!r.ok) throw new Error(`Filters fetch failed ${r.status}`);
  return r.json();
}

async function fetchFilesServer(q: string, sc: string, ex: string): Promise<FilesResponse> {
  const u = new URL(API_FILES);
  if (q) u.searchParams.set('q', q);
  if (sc && sc !== 'all') u.searchParams.set('scope', sc);
  if (ex && ex !== 'all') u.searchParams.set('ext', ex);
  const r = await fetch(u.toString(), { cache: 'no-store' });
  if (!r.ok) throw new Error(`Files fetch failed ${r.status}`);
  return r.json();
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
}

function renderList(container: HTMLElement, files: string[]) {
  container.innerHTML = '';
  const ul = el('ul', 'fl-ul');
  for (const f of files) {
    const li = el('li', 'fl-li');
    const badge = el('span', `fl-badge fl-${scopeOf(f)}`, scopeOf(f).toUpperCase());
    const path = el('span', 'fl-path', f);
    li.appendChild(badge);
    li.appendChild(path);
    ul.appendChild(li);
  }
  container.appendChild(ul);
}

function unique<T>(arr: T[]): T[] { return Array.from(new Set(arr)); }

export function mountFileListUI() {
  if (document.getElementById('file-list-ui')) return;
  const root = el('div', 'fl-root');
  root.id = 'file-list-ui';
  root.innerHTML = `
    <style>
      .fl-root{position:fixed;inset:auto 16px 16px auto;z-index:99999;width:min(720px,95vw);max-height:70vh;background:#0f172a;/* slate-900 */color:#e2e8f0;border:1px solid #334155;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.5);font:13px/1.4 ui-sans-serif,system-ui;}
      .fl-hd{display:flex;gap:8px;align-items:center;padding:10px 12px;border-bottom:1px solid #334155}
      .fl-hd h3{margin:0 8px 0 0;font-size:14px}
      .fl-hd input,.fl-hd select{background:#0b1220;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:6px 8px}
      .fl-hd button{background:#1d4ed8;color:#fff;border:0;border-radius:6px;padding:6px 10px;cursor:pointer}
      .fl-bd{padding:8px 12px;overflow:auto;max-height:55vh}
      .fl-ul{list-style:none;margin:0;padding:0}
      .fl-li{display:flex;gap:8px;align-items:center;padding:4px 0;border-bottom:1px dashed #1f2937}
      .fl-badge{font-size:10px;padding:2px 6px;border-radius:999px;border:1px solid #334155}
      .fl-frontend{background:#064e3b}
      .fl-backend{background:#4c0519}
      .fl-other{background:#3f3f46}
      .fl-path{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,monospace;white-space:pre-wrap;word-break:break-all}
    </style>`;

  const hdr = el('div', 'fl-hd');
  const title = el('h3', '', 'File Explorer (localhost:1234)');
  const search = el('input') as HTMLInputElement;
  search.placeholder = 'Search path…';
  const scope = el('select') as HTMLSelectElement;
  scope.innerHTML = '<option value="all">All</option><option value="frontend">Frontend</option><option value="backend">Backend</option>';
  const ext = el('select') as HTMLSelectElement;
  ext.innerHTML = '<option value="all">Any ext</option>';
  const refresh = el('button', '', 'Refresh');
  hdr.append(title, search, scope, ext, refresh);

  const body = el('div', 'fl-bd');
  root.append(hdr, body);
  document.body.appendChild(root);

  async function applyFilters() {
    const q = search.value.trim();
    const sc = scope.value as 'all' | 'frontend' | 'backend';
    const ex = ext.value;
    const data = await fetchFilesServer(q, sc, ex);
    renderList(body, (data.files || []).sort((a,b)=>a.localeCompare(b)));
  }

  async function load() {
    try {
      const f = await fetchFilters();
      const exts = (f.extensions || []).sort();
      ext.innerHTML = '<option value="all">Any ext</option>' + exts.map(e => `<option value="${e}">${e}</option>`).join('');
      await applyFilters();
    } catch (e) {
      body.innerHTML = `<div style="color:#f87171">Failed to load from ${API_BASE}: ${(e as Error).message}</div>`;
    }
  }

  refresh.onclick = load;
  search.oninput = () => { void applyFilters(); };
  scope.onchange = () => { void applyFilters(); };
  ext.onchange = () => { void applyFilters(); };
  void load();
}

// Auto-mount if imported directly
try { mountFileListUI(); } catch { /* no-op for SSR */ }
