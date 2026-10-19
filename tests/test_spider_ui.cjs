const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../frontend/web/halloween-spider.js'), 'utf8');

function fixture({ paused = false, obstacles = [] } = {}) {
  const frames = new Map(), timers = new Map(), listeners = {}, nodes = {};
  let id = 0, observer;
  const node = () => {
    const classes = new Set(), events = {};
    return { hidden: false, offsetWidth: 68, offsetHeight: 68, innerHTML: '', title: '',
      style: { setProperty() {} }, events, matches: () => false,
      classList: { contains: key => classes.has(key), add: key => classes.add(key), remove: key => classes.delete(key),
        toggle(key, yes) { if (yes) classes.add(key); else classes.delete(key); } },
      addEventListener(key, callback) { events[key] = callback; } };
  };
  const get = key => nodes[key] ||= node();
  const body = node(); if (paused) body.classList.add('motion-paused');
  const context = vm.createContext({
    document: { hidden: false, body, documentElement: { dataset: { theme: 'light' } },
      querySelector: get, querySelectorAll: () => obstacles,
      addEventListener(key, callback) { listeners[key] = callback; } },
    window: { matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {} },
    innerWidth: 800, innerHeight: 600,
    requestAnimationFrame(callback) { const token = ++id; frames.set(token, callback); return token; },
    cancelAnimationFrame(token) { frames.delete(token); },
    setTimeout(callback, delay) { const token = ++id; timers.set(token, { callback, delay }); return token; },
    clearTimeout(token) { timers.delete(token); },
    MutationObserver: class { constructor(callback) { observer = callback; } observe() {} },
  });
  vm.runInContext(source, context); listeners.DOMContentLoaded();
  return { get, frames, timers, context, sync: () => observer(),
    timer(delay) { const entry = [...timers].find(([, timer]) => timer.delay === delay); assert.ok(entry); timers.delete(entry[0]); entry[1].callback(); },
    step(time) { const entry = [...frames][0]; assert.ok(entry); frames.delete(entry[0]); entry[1](time); },
    key(key) { listeners.keydown({ key }); } };
}

test('hover pauses briefly and resumes without requiring pointerleave', () => {
  const ui = fixture(), spider = ui.get('#halloween-spider');
  ui.step(1);
  spider.events.pointerenter({ pointerType: 'mouse' });
  assert.equal(ui.frames.size, 0);
  ui.timer(1200);
  assert.equal(ui.frames.size, 1);
  ui.step(17); assert.equal(spider.classList.contains('is-crawling'), true);
});

test('touch does not leave spider stuck in a hover pause', () => {
  const ui = fixture();
  ui.get('#halloween-spider').events.pointerenter({ pointerType: 'touch' });
  assert.equal(ui.frames.size, 1); assert.equal(ui.timers.size, 0);
});

test('reduced movement visibly marks resting spider and resumes when disabled', () => {
  const ui = fixture({ paused: true }), spider = ui.get('#halloween-spider');
  assert.equal(ui.frames.size, 0); assert.equal(spider.classList.contains('is-resting'), true);
  assert.match(spider.title, /đang nghỉ/);
  ui.context.document.body.classList.remove('motion-paused'); ui.sync();
  assert.equal(ui.frames.size, 1); assert.equal(spider.classList.contains('is-resting'), false);
});

test('hug release resumes crawling and Escape ends a hug', () => {
  const ui = fixture(), spider = ui.get('#halloween-spider');
  spider.events.click({ detail: 1 });
  assert.equal(ui.get('#spider-hug').hidden, false); assert.equal(ui.frames.size, 0);
  ui.timer(3400);
  assert.equal(ui.get('#spider-hug').hidden, true); assert.equal(ui.frames.size, 1);
  spider.events.click({ detail: 1 }); ui.key('Escape');
  assert.equal(ui.get('#spider-hug').hidden, true); assert.equal(ui.frames.size, 1);
});

test('theme changes cancel a hug and hide the Halloween spider', () => {
  const ui = fixture(), spider = ui.get('#halloween-spider');
  spider.events.click({ detail: 1 });
  ui.context.document.documentElement.dataset.theme = 'dark'; ui.sync();
  assert.equal(spider.hidden, true); assert.equal(ui.get('#spider-hug').hidden, true);
  assert.equal(ui.frames.size, 0); assert.equal(ui.timers.size, 0);
});

test('spider relocates away from actionable controls instead of covering them', () => {
  const protectedRect = { left: 0, top: 90, right: 240, bottom: 220, width: 240, height: 130 };
  const ui = fixture({ obstacles: [{ getBoundingClientRect: () => protectedRect }] });
  const position = ui.get('#halloween-spider').style.transform;
  const [x, y] = [...position.matchAll(/([\d.]+)px/g)].map(match => Number(match[1]));
  const overlap = x < protectedRect.right + 8 && x + 68 > protectedRect.left - 8 && y < protectedRect.bottom + 8 && y + 68 > protectedRect.top - 8;
  assert.equal(overlap, false);
});
