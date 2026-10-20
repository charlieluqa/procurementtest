const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('/workspace/index.html', 'utf-8');

const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.error('No script tag'); process.exit(1); }
const js = scriptMatch[1];

function makeEl(tag = 'div', id) {
  const el = {
    tagName: tag,
    id: id || '',
    innerHTML: '',
    textContent: '',
    value: '',
    dataset: {},
    style: {},
    classList: {
      _set: new Set(),
      add(c) { this._set.add(c); },
      remove(c) { this._set.delete(c); },
      toggle(c, force) { if (force === true) this._set.add(c); else if (force === false) this._set.delete(c); else { if (this._set.has(c)) this._set.delete(c); else this._set.add(c); } },
    },
    _listeners: [],
    addEventListener(type, fn) { this._listeners.push({type, fn}); },
    appendChild(ch) {
      if (ch && typeof ch.outerHTML === 'string') {
        this.innerHTML += ch.outerHTML;
      } else if (ch && ch.innerHTML !== undefined) {
        // simple fallback: use innerHTML of child as tagless content? No, let's build outerHTML from tagName/innerHTML
        const oh = `<${ch.tagName || 'div'}>${ch.innerHTML || ch.textContent || ''}</${ch.tagName || 'div'}>`;
        this.innerHTML += oh;
      }
    },
    children: [],
    scrollIntoView() {},
    get outerHTML() {
      const cls = [...this.classList._set].join(' ');
      const clsAttr = cls ? ` class="${cls}"` : '';
      const idAttr = this.id ? ` id="${this.id}"` : '';
      return `<${this.tagName}${idAttr}${clsAttr}>${this.innerHTML}</${this.tagName}>`;
    },
    querySelectorAll(sel) { return []; },
  };
  return el;
}

const document = {
  _els: new Map(),
  getElementById(id) {
    if (!this._els.has(id)) this._els.set(id, makeEl('div', id));
    return this._els.get(id);
  },
  querySelectorAll(sel) {
    const els = [];
    if (sel === '#viewToggle button') {
      // view toggle buttons: create minimal stubs
      ['findings','contracts','invoices','tests'].forEach(v => {
        const b = makeEl('button');
        b.dataset = { view: v };
        b.classList = {
          _set: new Set(v === 'findings' ? ['active'] : []),
          add(c){this._set.add(c);}, remove(c){this._set.delete(c);}, toggle(c,force){}
        };
        els.push(b);
      });
    }
    return els;
  },
  createElement(tag) { return makeEl(tag); },
};

const window = { document, scrollTo(){}, addEventListener(){} };
const sandbox = { console, document, window, Date, Math, JSON, setTimeout, clearTimeout };
vm.createContext(sandbox);

try {
  vm.runInContext(js, sandbox, { timeout: 5000 });
} catch (e) {
  console.error('JS runtime error:', e.message);
  process.exit(1);
}

const m = document._els.get('metrics');
if (!m || !m.innerHTML.includes('Annual contract spend')) {
  console.error('Metrics not rendered'); process.exit(1);
}

const fb = document._els.get('findingsBody');
if (!fb || !fb.innerHTML) {
  console.error('Findings table not rendered'); process.exit(1);
}

const cb = document._els.get('contractsBody');
if (!cb || !cb.innerHTML.includes('RUT-001')) {
  console.error('Contracts table not rendered'); process.exit(1);
}

const ib = document._els.get('invoicesBody');
if (!ib || !ib.innerHTML.includes('INV-')) {
  console.error('Invoices table not rendered'); process.exit(1);
}

console.log('Headless JS runtime check passed: tables and metrics rendered successfully.');
