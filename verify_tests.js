const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('/workspace/index.html', 'utf-8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.error('No script'); process.exit(1); }
const js = scriptMatch[1];

function makeEl(tag = 'div', id) {
  const el = {
    tagName: tag, id: id || '',
    innerHTML: '', textContent: '', value: '',
    dataset: {}, style: {},
    classList: {
      _set: new Set(),
      add(c){ this._set.add(c); },
      remove(c){ this._set.delete(c); },
      toggle(c,force){ if (force===true)this._set.add(c); else if(force===false)this._set.delete(c); else { if(this._set.has(c))this._set.delete(c); else this._set.add(c); } },
    },
    _listeners: [],
    addEventListener(type, fn){ this._listeners.push({type,fn}); },
    appendChild(ch){ this.innerHTML += (ch && ch.outerHTML ? ch.outerHTML : `<${ch?.tagName||'div'}>${ch?.innerHTML||ch?.textContent||''}</${ch?.tagName||'div'}>`); },
    children: [], scrollIntoView(){},
    get outerHTML() {
      const cls = [...this.classList._set].join(' ');
      return `<${this.tagName}${this.id?` id="${this.id}"`:''}${cls?` class="${cls}"`:''}>${this.innerHTML}</${this.tagName}>`;
    },
    querySelectorAll(sel) {
      if (sel === '#viewToggle button') {
        return ['findings','contracts','invoices','tests'].map(v => {
          const b = makeEl('button');
          b.dataset = { view: v };
          b.classList = {
            _set: new Set(v==='findings'?['active']:[]),
            add(c){this._set.add(c);}, remove(c){this._set.delete(c);}, toggle(){}
          };
          return b;
        });
      }
      return [];
    },
  };
  return el;
}

const document = {
  _els: new Map(),
  getElementById(id) {
    if (!this._els.has(id)) this._els.set(id, makeEl('div', id));
    return this._els.get(id);
  },
  createElement(tag){ return makeEl(tag); },
  querySelectorAll(sel){ return this.getElementById('viewToggle').querySelectorAll(sel); },
};

const sandbox = { console, document, window: { document, scrollTo(){}, addEventListener(){} }, Date, Math, JSON, setTimeout, clearTimeout };
vm.createContext(sandbox);
vm.runInContext(js, sandbox, { timeout: 5000 });

// Run the test suite by firing the runTests button click
const btn = document._els.get('runTests');
const clickEvt = { target: btn };
// Find and invoke click handler
const handler = btn._listeners.find(l => l.type === 'click');
if (!handler) { console.error('No click handler on runTests'); process.exit(1); }
handler.fn();

const output = document._els.get('testOutput').textContent;
console.log(output);
if (!output.includes('passed') || output.includes('failed') && !output.includes('0 failed')) {
  // Allow 0 failed
  const m = output.match(/(\d+) passed, (\d+) failed/);
  if (!m) { console.error('Could not parse test results'); process.exit(1); }
  if (parseInt(m[2],10) > 0) { console.error('Tests had failures'); process.exit(1); }
}
console.log('All embedded tests passed in headless simulation.');
