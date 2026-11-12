// Synthetic, no-network browser test for SaveOnSub Meta/GA4 consent behavior.
// Exercises real source JS inside a Node VM. No credentials, customers or external requests.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const pixelSrc = fs.readFileSync(path.join(root, 'assets/meta-pixel.js'), 'utf8');
const gaSrc = fs.readFileSync(path.join(root, 'assets/ga4.js'), 'utf8');

function makeBrowser(initialConsent, privacy = {}) {
  const items = new Map(initialConsent ? [['sos_ads_consent_v1', initialConsent]] : []);
  const elements = new Map();
  const scripts = [];
  const events = new Map();
  const on = (name, fn) => { if (!events.has(name)) events.set(name, []); events.get(name).push(fn); };
  const emit = evt => { for (const fn of events.get(evt.type) || []) fn(evt); };
  const createElement = tag => ({
    tagName: tag.toUpperCase(), id: '', className: '', style: {},
    textContent: '', innerHTML: '', children: [], attributes: {},
    setAttribute(name, value) { this.attributes[name] = String(value); },
    appendChild(node) { this.children.push(node); },
    remove() { if (this.id) elements.delete(this.id); }
  });
  const document = {
    readyState: 'complete',
    documentElement: { lang: 'bn' },
    cookie: '',
    createElement, addEventListener: on,
    getElementById: id => elements.get(id) || null,
    querySelectorAll: () => [],
    head: { appendChild(node) { if (node.tagName === 'SCRIPT') scripts.push(node.src || ''); } },
    body: { appendChild(node) { if (node.id) elements.set(node.id, node); } }
  };
  const storage = {
    getItem: key => items.has(key) ? items.get(key) : null,
    setItem: (key, val) => { items.set(key, String(val)); },
    removeItem: key => { items.delete(key); }
  };
  const ctx = {
    document, navigator: { globalPrivacyControl: Boolean(privacy.gpc), doNotTrack: privacy.dnt ? '1' : '0' },
    localStorage: storage, location: { pathname: '/', search: '' },
    CustomEvent: class CustomEvent { constructor(type, options = {}) { this.type = type; this.detail = options.detail; } },
    addEventListener: on, dispatchEvent: emit, setTimeout, clearTimeout,
    console
  };
  ctx.window = ctx;
  ctx.doNotTrack = privacy.dnt ? '1' : '0';
  vm.createContext(ctx);
  vm.runInContext(pixelSrc, ctx, { filename: 'meta-pixel.js' });
  vm.runInContext(gaSrc, ctx, { filename: 'ga4.js' });
  return { ctx, scripts, items, elements, emit };
}

function run() {
  const fresh = makeBrowser();
  assert.equal(fresh.ctx.document.getElementById('sos-ads-consent'), null, 'no cookie banner');
  assert.equal(fresh.scripts.filter(x => x.includes('connect.facebook.net')).length, 1, 'Pixel loads by default');
  assert.equal(fresh.scripts.filter(x => x.includes('googletagmanager.com/gtag')).length, 1, 'GA4 loads by default');
  const adTrack = () => {
    fresh.emit(new fresh.ctx.CustomEvent('sos:track', {
      detail: { event: 'sos_whatsapp_click', link_text: 'CTA' }
    }));
  };
  adTrack();
  const queue = fresh.ctx.fbq.queue;
  assert.ok(queue.some(args => args[0] === 'track' && args[1] === 'Contact'), 'Meta Contact expected');
  assert.ok(fresh.ctx.dataLayer.some(args => args[0] === 'event' && args[1] === 'whatsapp_click'), 'GA4 click expected');

  fresh.ctx.sosAdsOptOut();
  assert.equal(fresh.items.get('sos_ads_consent_v1'), 'denied');
  assert.ok(queue.some(args => args[0] === 'consent' && args[1] === 'revoke'), 'Pixel revoke expected');
  assert.ok(fresh.ctx.dataLayer.some(args => args[0] === 'consent' && args[1] === 'update' && args[2].analytics_storage === 'denied'), 'GA4 deny expected');
  const beforeQueue = queue.length;
  const beforeLayer = fresh.ctx.dataLayer.length;
  adTrack();
  assert.equal(queue.length, beforeQueue, 'no Meta event after opt-out');
  assert.equal(fresh.ctx.dataLayer.length, beforeLayer, 'no GA4 event after opt-out');

  fresh.ctx.sosAdsOptIn();
  assert.ok(queue.some(args => args[0] === 'consent' && args[1] === 'grant'), 'Pixel re-grant expected');
  adTrack();
  assert.ok(queue.length > beforeQueue, 'Meta event resumes after opt-in');

  assert.equal(makeBrowser('denied').scripts.length, 0, 'Opt-out survives reload');
  assert.equal(makeBrowser('granted').scripts.length, 2, 'Older explicit grant still loads');
  assert.equal(makeBrowser(null, { gpc: true }).scripts.length, 0, 'GPC blocks both trackers');
  assert.equal(makeBrowser(null, { dnt: true }).scripts.length, 0, 'DNT blocks both trackers');

  process.stdout.write('PASS: synthetic Meta Pixel + GA4 opt-out lifecycle\n');
}
run();
