const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../frontend/web/app.js'), 'utf8');
const cameraSource = fs.readFileSync(path.join(__dirname, '../frontend/web/camera.js'), 'utf8');
function element(extra = {}) {
  return { innerHTML: '', textContent: '', hidden: false, value: '', disabled: false, dataset: {}, options: [],
    focus() { this.focused = true; }, showModal() { this.open = true; this.modalCount = (this.modalCount || 0) + 1; }, close() { this.open = false; },
    listeners: {}, addEventListener(name, handler) { this.listeners[name] = handler; },
    classList: { add() {}, remove() {}, toggle() {} }, ...extra };
}
function setup(fixtures = {}, overrides = {}) {
  const nodes = {}, lists = {}, requests = [], revoked = [];
  const get = selector => nodes[selector] ||= element();
  const context = vm.createContext({
    document: { querySelector: get, querySelectorAll: selector => lists[selector] || [], addEventListener() {}, removeEventListener() {} },
    localStorage: { getItem() { return ''; }, setItem() {}, removeItem() {} }, AbortController, FormData, URLSearchParams,
    URL: { createObjectURL() { return 'blob:test-preview'; }, revokeObjectURL(url) { revoked.push(url); } },
    setTimeout() { return 1; }, clearTimeout() {}, confirm: () => true, prompt: () => null,
    fetch: async (url, options) => { requests.push({ url, options }); return { ok: true, json: async () => fixtures[url] || {} }; },
    ...overrides,
  });
  vm.runInContext(cameraSource, context);
  vm.runInContext(source + '\nthis.ui = { state, RENDER, bindUpload, runPending, api, previewCleanups, requestReauthentication, doSessionLogin };', context);
  context.ui.state.user = { username: 'admin', role: 'admin' };
  vm.runInContext('showView = async () => {};', context);
  return { ...context.ui, context, get, nodes, lists, requests, revoked };
}

test('review badge uses review KPI even when recent logs contain other tickets', async () => {
  const ui = setup({ '/operations/summary': { kpis: { review_tickets: 2 }, health: { code: 'NORMAL' } },
    '/logs?limit=6': { total: 50, items: [{ ticket_id: '<script>x</script>', status: 'COMPLETED' }] },
    '/tickets/active': { items: [] } });
  await ui.RENDER.dashboard();
  assert.equal(ui.get('#review-badge').textContent, 2);
  assert.equal(ui.get('#review-badge').hidden, false);
  const html = ui.get('#view-content').innerHTML;
  assert.ok(html.includes('&lt;script&gt;x&lt;/script&gt;'));
  assert.equal((html.match(/<th>/g) || []).length, 5);
  assert.ok(!html.includes('AI Vision'));
});

test('dragged image is submitted, cleared, and its preview URL released', async () => {
  const ui = setup({ '/vehicle/entry': { result: { ticket_id: 'T1', plate_entry: '59-B1 069.99' } } });
  ui.state.view = 'entry';
  const zone = element();
  ui.get('#entry-drop').closest = () => zone;
  await ui.RENDER.entry();
  const image = new File(['image'], 'plate.png', { type: 'image/png' });
  zone.listeners.drop({ preventDefault() {}, dataTransfer: { files: [image] } });
  assert.ok(ui.get('#entry-preview').innerHTML.includes('blob:test-preview'));
  await ui.get('#entry-submit').listeners.click();
  const sent = ui.requests.find(request => request.url === '/vehicle/entry');
  assert.equal(sent.options.body.get('file').name, 'plate.png');
  assert.equal(ui.get('#entry-preview').innerHTML, '');
  assert.equal(ui.get('#entry-submit').disabled, false);
  assert.deepEqual(ui.revoked, ['blob:test-preview']);
});

test('exit selection excludes tickets needing review', async () => {
  const ui = setup({ '/tickets/active': { items: [
    { ticket_id: 'ACTIVE-TICKET', plate_entry: '59-B1 069.99', status: 'IN_PARKING' },
    { ticket_id: 'REVIEW-TICKET', plate_entry: '59-B2 123.45', status: 'NEEDS_REVIEW' },
  ] } });
  ui.state.view = 'exit';
  ui.get('#exit-drop').closest = () => element();
  await ui.RENDER.exit();
  assert.ok(ui.get('#view-content').innerHTML.includes('ACTIVE-TICKET'));
  assert.ok(!ui.get('#view-content').innerHTML.includes('REVIEW-TICKET'));
});

test('log search matches exit plate as well as entry plate and ticket ID', async () => {
  const ui = setup({ '/logs?limit=500': { items: [{ ticket_id: 'T1', plate_entry: '59-B1 069.99', plate_exit: '59-B2 123.45' }] } });
  ui.state.view = 'logs';
  await ui.RENDER.logs();
  ui.get('#log-search').value = 'B2';
  ui.get('#log-search').listeners.input();
  assert.ok(ui.get('#log-tbody').innerHTML.includes('T1'));
  ui.get('#log-search').value = 'nonexistent';
  ui.get('#log-search').listeners.input();
  assert.ok(!ui.get('#log-tbody').innerHTML.includes('T1'));
});

for (const isActive of [true, false]) {
  test(`account active toggle sends ${!isActive} when current state is ${isActive}`, async () => {
    const ui = setup({ '/admin/users': { items: [{ username: 'operator', role: 'operator', is_active: isActive }] } });
    ui.state.view = 'admin';
    const btn = element({ dataset: { u: 'operator', op: 'active' } });
    ui.lists['[data-op]'] = [btn];
    await ui.RENDER.admin();
    await btn.listeners.click();
    const sent = ui.requests.find(request => request.url.endsWith('/active'));
    assert.equal(sent.options.body.get('is_active'), String(!isActive));
  });
}

test('pending action ignores a second click while its request is in progress', async () => {
  const ui = setup();
  const btn = element();
  let release, calls = 0;
  const action = () => { calls++; return new Promise(resolve => { release = resolve; }); };
  const first = ui.runPending(btn, 'Processing', action);
  await ui.runPending(btn, 'Processing', action);
  assert.equal(calls, 1);
  release(); await first;
  assert.equal(btn.disabled, false);
});

test('network failure produces an actionable message', async () => {
  const ui = setup({}, { fetch: async () => { throw new TypeError('Failed to fetch'); } });
  await assert.rejects(ui.api('/logs'), /Không kết nối được máy chủ/);
});

test('navigation abort preserves AbortError instead of showing connection failure', async () => {
  const error = new Error('aborted'); error.name = 'AbortError';
  const ui = setup({}, { fetch: async () => { throw error; } });
  await assert.rejects(ui.api('/logs'), ex => ex === error);
});

test('HTML returned with HTTP 200 is rejected before rendering', async () => {
  const ui = setup({}, { fetch: async () => ({ ok: true, json: async () => { throw new SyntaxError(); } }) });
  await assert.rejects(ui.api('/logs'), /dữ liệu không hợp lệ/);
});

test('provider error text reaches the user without being replaced by a TypeError', async () => {
  const ui = setup({}, { fetch: async () => ({ ok: false, json: async () => ({ error: { message: 'AI chưa cấu hình' } }) }) });
  await assert.rejects(ui.api('/ocr'), /AI chưa cấu hình/);
});

for (const [name, type, size] of [
  ['plate.gif', 'image/gif', 10], ['plate.bmp', 'image/bmp', 10],
  ['plate.png', 'text/plain', 10], ['plate.jpg', 'image/jpeg', 0],
  ['plate.jpg', 'image/jpeg', 10 * 1024 * 1024 + 1],
]) {
  test(`invalid upload rejected before preview: ${name}, ${type}, ${size} bytes`, async () => {
    const ui = setup();
    const zone = element(); ui.get('#entry-drop').closest = () => zone;
    const upload = ui.bindUpload('entry');
    zone.listeners.drop({ preventDefault() {}, dataTransfer: { files: [{ name, type, size }] } });
    assert.equal(upload.getFile(), null);
    assert.equal(ui.get('#entry-preview').innerHTML, '');
    assert.equal(ui.get('#toast').hidden, false);
  });
}

test('removing a selected image clears submission state and releases the preview', () => {
  const ui = setup(); const zone = element(); ui.get('#entry-drop').closest = () => zone;
  const upload = ui.bindUpload('entry');
  zone.listeners.drop({ preventDefault() {}, dataTransfer: { files: [new File(['data'], 'plate.webp', { type: 'image/webp' })] } });
  assert.ok(upload.getFile());
  ui.get('#entry-remove').listeners.click();
  assert.equal(upload.getFile(), null);
  assert.deepEqual(ui.revoked, ['blob:test-preview']);
});

test('viewer cannot submit an entry even if the handler is triggered directly', async () => {
  const ui = setup(); ui.state.user.role = 'viewer'; ui.state.view = 'entry';
  ui.get('#entry-drop').closest = () => element();
  await ui.RENDER.entry();
  await ui.get('#entry-submit').listeners.click();
  assert.ok(ui.get('#view-content').innerHTML.includes('disabled'));
  assert.equal(ui.requests.length, 0);
});

test('failed action restores the button so the user can retry', async () => {
  const ui = setup(); const btn = element({ innerHTML: 'Submit' });
  await ui.runPending(btn, 'Loading', async () => { throw new Error('Temporary failure'); });
  assert.equal(btn.disabled, false);
  assert.equal(btn.innerHTML, 'Submit');
  assert.equal(ui.get('#toast').textContent, 'Temporary failure');
});

function cameraFixture(prefix = 'entry', mediaOverride = {}) {
  const ui = setup();
  ui.get(`#${prefix}-drop`).closest = () => element();
  let stops = 0, requests = [], drawn = null;
  const track = { stop() { stops++; }, addEventListener() {}, getSettings() { return { deviceId: 'usb-1' }; } };
  const stream = { getTracks: () => [track], getVideoTracks: () => [track] };
  const video = ui.get(`#${prefix}-camera-video`);
  Object.assign(video, { videoWidth: 3840, videoHeight: 2160, readyState: 4, play: async () => {}, pause() {} });
  const canvas = { getContext: () => ({ drawImage(...args) { drawn = args; } }),
    toBlob(callback) { callback(new Blob(['jpeg-frame'], { type: 'image/jpeg' })); } };
  ui.context.document.createElement = () => canvas;
  ui.context.File = File;
  ui.context.isSecureContext = true;
  ui.context.navigator = { mediaDevices: {
    getUserMedia: async constraints => { requests.push(constraints); return stream; },
    enumerateDevices: async () => [{ kind: 'videoinput', deviceId: 'usb-1', label: 'USB <camera>' }],
    ...mediaOverride,
  } };
  const upload = ui.bindUpload(prefix);
  return { ui, upload, video, canvas, stream, requests, get stops() { return stops; }, get drawn() { return drawn; } };
}

for (const prefix of ['entry', 'exit']) {
  test(`real camera ${prefix} capture becomes a JPEG upload and releases the device`, async () => {
    const fixture = cameraFixture(prefix), { ui, upload, canvas, video } = fixture;
    await ui.get(`#${prefix}-camera-open`).listeners.click();
    assert.equal(fixture.requests[0].audio, false);
    assert.equal(fixture.requests[0].video.facingMode.ideal, 'environment');
    assert.equal(video.srcObject, fixture.stream);
    assert.equal(ui.get(`#${prefix}-camera-shutter`).disabled, false);
    assert.match(ui.get(`#${prefix}-camera-devices`).innerHTML, /USB &lt;camera&gt;/);
    await ui.get(`#${prefix}-camera-shutter`).listeners.click();
    assert.equal(upload.getFile().type, 'image/jpeg');
    assert.match(upload.getFile().name, /^camera-.*\.jpg$/);
    assert.equal(canvas.width, 2560); assert.equal(canvas.height, 1440);
    assert.equal(fixture.drawn[0], video);
    assert.equal(fixture.stops, 1);
    assert.equal(video.srcObject, null);
    assert.equal(ui.get(`#${prefix}-camera-panel`).hidden, true);
    assert.equal(ui.requests.length, 0, 'capturing does not create a ticket or upload automatically');
  });
}

for (const action of ['close', 'navigate']) {
  test(`camera granted after ${action} is immediately released`, async () => {
    let grant;
    const fixture = cameraFixture('entry', { getUserMedia: () => new Promise(resolve => { grant = resolve; }) });
    const pending = fixture.ui.get('#entry-camera-open').listeners.click();
    if (action === 'close') fixture.ui.get('#entry-camera-close').listeners.click();
    else fixture.ui.previewCleanups.splice(0).forEach(cleanup => cleanup());
    grant(fixture.stream); await pending;
    assert.equal(fixture.stops, 1);
    assert.equal(fixture.video.srcObject, null);
    assert.equal(fixture.upload.getFile(), null);
    assert.equal(fixture.ui.get('#entry-camera-panel').hidden, true);
  });
}

test('switching camera releases the previous stream before requesting a device', async () => {
  const fixture = cameraFixture(), { ui } = fixture;
  await ui.get('#entry-camera-open').listeners.click();
  ui.get('#entry-camera-devices').value = 'rear-2';
  await ui.get('#entry-camera-devices').listeners.change();
  assert.equal(fixture.stops, 1);
  assert.equal(fixture.requests[1].video.deviceId.exact, 'rear-2');
  ui.previewCleanups.splice(0).forEach(cleanup => cleanup());
  assert.equal(fixture.stops, 2);
});

for (const [name, message] of [['NotAllowedError', 'quyền camera'], ['NotFoundError', 'Không tìm thấy camera'], ['NotReadableError', 'ứng dụng khác']]) {
  test(`camera reports actionable ${name} and allows retry`, async () => {
    const error = new Error('raw-device-error'); error.name = name;
    const fixture = cameraFixture('entry', { getUserMedia: async () => { throw error; } });
    await fixture.ui.get('#entry-camera-open').listeners.click();
    assert.match(fixture.ui.get('#entry-camera-message').textContent, new RegExp(message));
    assert.equal(fixture.ui.get('#entry-camera-shutter').disabled, true);
    assert.equal(fixture.ui.get('#entry-camera-open').disabled, false);
    assert.equal(fixture.video.srcObject, null);
  });
}

test('camera does not capture before the first frame arrives', async () => {
  const fixture = cameraFixture(), { ui, video } = fixture;
  video.readyState = 0; video.videoWidth = 0; video.videoHeight = 0;
  await ui.get('#entry-camera-open').listeners.click();
  await ui.get('#entry-camera-shutter').listeners.click();
  assert.equal(fixture.upload.getFile(), null);
  assert.equal(fixture.drawn, null);
  assert.match(ui.get('#entry-camera-message').textContent, /Chờ camera/);
});

test('failed frame encoding keeps the camera open and preserves the error', async () => {
  const fixture = cameraFixture(), { ui, canvas } = fixture;
  canvas.toBlob = callback => callback(null);
  await ui.get('#entry-camera-open').listeners.click();
  await ui.get('#entry-camera-shutter').listeners.click();
  assert.equal(fixture.upload.getFile(), null);
  assert.equal(ui.get('#entry-camera-panel').hidden, false);
  assert.equal(ui.get('#entry-camera-shutter').disabled, false);
  assert.match(ui.get('#entry-camera-message').textContent, /chưa tạo được ảnh/);
});

test('closing camera while encoding prevents a late photo replacing the selected file', async () => {
  const fixture = cameraFixture(), { ui, canvas } = fixture;
  let encoded;
  canvas.toBlob = callback => { encoded = callback; };
  await ui.get('#entry-camera-open').listeners.click();
  const pending = ui.get('#entry-camera-shutter').listeners.click();
  ui.get('#entry-camera-close').listeners.click();
  encoded(new Blob(['late-frame'], { type: 'image/jpeg' })); await pending;
  assert.equal(fixture.upload.getFile(), null);
  assert.equal(fixture.stops, 1);
});

test('scan only calls OCR, escapes plate text, and asks for image comparison', async () => {
  const ui = setup({ '/ocr': { ocr: { text: '<plate>59-B1 069.99' } } });
  const zone = element(); ui.get('#entry-drop').closest = () => zone;
  ui.bindUpload('entry');
  zone.listeners.drop({ preventDefault() {}, dataTransfer: { files: [new File(['image'], 'plate.jpg', { type: 'image/jpeg' })] } });
  await ui.get('#entry-scan').listeners.click();
  assert.equal(ui.requests.length, 1); assert.equal(ui.requests[0].url, '/ocr');
  assert.match(ui.get('#entry-scan-result').innerHTML, /&lt;plate&gt;/);
  assert.match(ui.get('#entry-scan-result').innerHTML, /Cần đối chiếu ảnh/);
  assert.equal(ui.get('#entry-scan').disabled, false);
});

test('OCR for a replaced photo is aborted and cannot overwrite the newer photo result', async () => {
  const ui = setup(); let resolve;
  const zone = element(); ui.get('#entry-drop').closest = () => zone;
  ui.bindUpload('entry');
  const drop = name => zone.listeners.drop({ preventDefault() {}, dataTransfer: { files: [new File(['image'], name, { type: 'image/jpeg' })] } });
  drop('first.jpg');
  let signal;
  ui.context.fetch = (_, options) => { signal = options.signal; return new Promise(done => { resolve = done; }); };
  const pending = ui.get('#entry-scan').listeners.click();
  drop('second.jpg');
  assert.equal(signal.aborted, true);
  resolve({ ok: true, json: async () => ({ ocr: { text: 'OLD PLATE' } }) }); await pending;
  assert.equal(ui.get('#entry-scan-result').hidden, true);
  assert.equal(ui.get('#entry-scan-result').innerHTML, '');
  assert.equal(ui.get('#entry-scan').disabled, false);
});

const expiredResponse = () => ({ ok: false, status: 401, json: async () => ({ detail: 'Unauthorized' }) });
const submitEvent = { preventDefault() {} };

test('expired session stops camera and preserves the selected photo and manual plate', async () => {
  const fixture = cameraFixture(), { ui, upload } = fixture;
  const file = new File(['image'], 'plate.jpg', { type: 'image/jpeg' });
  ui.get('#entry-camera-native').files = [file]; ui.get('#entry-camera-native').listeners.change();
  ui.get('#entry-plate').value = '59-B1 069.99';
  await ui.get('#entry-camera-open').listeners.click();
  ui.state.token = 'expired'; ui.context.fetch = async () => expiredResponse();
  await assert.rejects(ui.api('/ocr', { method: 'POST' }), /Phiên đăng nhập đã hết hạn/);
  assert.equal(ui.state.sessionExpired, true); assert.equal(ui.state.token, '');
  assert.equal(ui.get('#session-dialog').open, true);
  assert.equal(ui.get('#session-password').focused, true);
  assert.equal(upload.getFile(), file);
  assert.equal(ui.get('#entry-preview').hidden, false);
  assert.equal(ui.get('#entry-plate').value, '59-B1 069.99');
  assert.equal(fixture.stops, 1); assert.deepEqual(ui.revoked, []);
});

test('reauthentication retains the photo and does not automatically repeat a ticket write', async () => {
  const fixture = cameraFixture(), { ui, upload } = fixture;
  const file = new File(['image'], 'plate.jpg', { type: 'image/jpeg' });
  ui.get('#entry-camera-native').files = [file]; ui.get('#entry-camera-native').listeners.change();
  const requests = [];
  ui.context.fetch = async url => {
    requests.push(url);
    return url === '/auth/login' ? { ok: true, json: async () => ({ access_token: 'fresh-token', user: { username: 'admin', role: 'admin' } }) } : expiredResponse();
  };
  ui.state.view = 'entry'; ui.state.token = 'expired';
  await assert.rejects(ui.api('/vehicle/entry', { method: 'POST' }));
  ui.get('#session-password').value = 'example-password';
  await ui.doSessionLogin(submitEvent);
  assert.deepEqual(requests, ['/vehicle/entry', '/auth/login']);
  assert.equal(ui.state.token, 'fresh-token'); assert.equal(ui.state.sessionExpired, false);
  assert.equal(ui.get('#session-dialog').open, false);
  assert.equal(ui.get('#session-password').value, '');
  assert.equal(upload.getFile(), file);
});

test('incorrect reauthentication password keeps the dialog open and clears the password', async () => {
  const ui = setup({}, { fetch: async () => expiredResponse() });
  ui.requestReauthentication(); ui.get('#session-password').value = 'wrong-password';
  await ui.doSessionLogin(submitEvent);
  assert.equal(ui.state.sessionExpired, true); assert.equal(ui.state.token, '');
  assert.equal(ui.get('#session-dialog').open, true);
  assert.match(ui.get('#session-error').textContent, /mật khẩu không đúng/);
  assert.equal(ui.get('#session-password').value, '');
  assert.equal(ui.get('#session-submit').disabled, false);
});

test('permission denial does not expire an otherwise valid login', async () => {
  const ui = setup({}, { fetch: async () => ({ ok: false, status: 403, json: async () => ({ detail: 'Forbidden' }) }) });
  ui.state.token = 'valid-token';
  await assert.rejects(ui.api('/admin/users'), /Forbidden/);
  assert.equal(ui.state.token, 'valid-token'); assert.equal(ui.state.sessionExpired, false);
  assert.notEqual(ui.get('#session-dialog').open, true);
});

test('simultaneous expired requests open one reauthentication dialog', async () => {
  const ui = setup(); const replies = [];
  ui.state.token = 'expired';
  ui.context.fetch = () => new Promise(resolve => replies.push(resolve));
  const first = ui.api('/logs').catch(error => error), second = ui.api('/tickets/active').catch(error => error);
  replies[0](expiredResponse()); replies[1](expiredResponse()); await Promise.all([first, second]);
  assert.equal(ui.get('#session-dialog').modalCount, 1);
});

test('late unauthorized response from an old token cannot invalidate the refreshed session', async () => {
  const ui = setup(); let finish;
  ui.state.token = 'old-token';
  ui.context.fetch = () => new Promise(resolve => { finish = resolve; });
  const pending = ui.api('/logs').catch(error => error);
  ui.requestReauthentication();
  ui.context.fetch = async () => ({ ok: true, json: async () => ({ access_token: 'new-token', user: { username: 'admin', role: 'admin' } }) });
  await ui.doSessionLogin(submitEvent);
  finish(expiredResponse()); await pending;
  assert.equal(ui.state.token, 'new-token'); assert.equal(ui.state.sessionExpired, false);
  assert.equal(ui.get('#session-dialog').open, false);
});

test('reauthentication applies a downgraded role without permitting a ticket write', async () => {
  const ui = setup({ '/auth/login': { access_token: 'viewer-token', user: { username: 'admin', role: 'viewer' } } });
  ui.requestReauthentication(); await ui.doSessionLogin(submitEvent);
  assert.equal(ui.get('#nav-admin').hidden, true);
  assert.equal(ui.get('#entry-submit').disabled, true);
  assert.equal(ui.get('#exit-submit').disabled, true);
});

test('login failure before an authenticated user exists does not open recovery dialog', async () => {
  const ui = setup({}, { fetch: async () => expiredResponse() }); ui.state.user = null;
  await assert.rejects(ui.api('/auth/me'), /Phiên đăng nhập/);
  assert.notEqual(ui.get('#session-dialog').open, true);
  await assert.rejects(ui.api('/auth/login', { method: 'POST' }), /mật khẩu không đúng/);
});
