'use strict';

const TOKEN_KEY = 'its_token';

const STATUS = {
  IN_PARKING: ['Đang trong bãi', 'info'],
  COMPLETED: ['Đã hoàn tất', 'success'],
  NEEDS_REVIEW: ['Cần kiểm tra', 'warning'],
  CANCELLED: ['Đã hủy', 'danger'],
};
const MATCH = {
  MATCH: ['Khớp', 'success'],
  MISMATCH: ['Lệch biển', 'danger'],
  PENDING: ['Chờ đối chiếu', 'warning'],
  RESOLVED_MATCH: ['Đã xác nhận khớp', 'success'],
  RESOLVED_APPROVED: ['Đã duyệt ra', 'success'],
  RESOLVED_REJECTED: ['Từ chối ra', 'danger'],
};
const ROLE = { admin: 'Quản trị viên', operator: 'Điều hành', viewer: 'Quan sát' };

const state = { token: localStorage.getItem(TOKEN_KEY) || '', user: null, sessionExpired: false, view: 'dashboard', viewVersion: 0, controller: null, motionPaused: false, theme: localStorage.getItem('its_theme') === 'light' ? 'light' : 'dark' };

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const ICONS = {
  dashboard: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  entry: '<path d="M3 12h14m-5-5 5 5-5 5M20 4v16"/>',
  exit: '<path d="M21 12H7m5-5-5 5 5 5M4 4v16"/>',
  review: '<path d="m12 3 10 18H2L12 3Z"/><path d="M12 9v5m0 3v.2"/>',
  logs: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6m-6 4h6m-6 4h4"/>',
  users: '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3m1-16a3 3 0 0 1 0 6m2 4a5 5 0 0 1 3 5"/>',
  logout: '<path d="M9 4H4v16h5m4-13 5 5-5 5m-5-5h13"/>',
  refresh: '<path d="M20 7v5h-5M4 17v-5h5m11-1a8 8 0 0 0-14-5M4 13a8 8 0 0 0 14 5"/>',
  car: '<path d="m5 7 2-4h10l2 4 2 3v8H3v-8l2-3Zm0 0h14M3 14h18M6 18v3m12-3v3m-12-10h2m8 0h2"/>',
  check: '<path d="m5 12 4 4L19 6"/><circle cx="12" cy="12" r="10"/>',
  upload: '<path d="M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5"/>',
  search: '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
  snow: '<path d="M12 2v20M3.3 7l17.4 10M3.3 17 20.7 7M8 4l4 3 4-3M8 20l4-3 4 3M3 11l4-2V5m14 8-4 2v4M3 13l4 2v4m14-8-4-2V5"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
  moon: '<path d="M20.5 13.2A9 9 0 0 1 10.8 3.5a9 9 0 1 0 9.7 9.7Z"/>',
  sparkle: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/>',
  camera: '<path d="m8 6 2-3h4l2 3h5v14H3V6h5Z"/><circle cx="12" cy="13" r="4"/>',
};
function icon(name) { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.car}</svg>`; }
function winterImage(name, className = '') {
  return `<img class="${className}" src="${themeAsset(name)}" data-winter-art="${name}" alt="" aria-hidden="true" />`;
}
function themeAsset(name) {
  const lightAssets = { 'winter-scene': 'halloween-scene', 'winter-snowman': 'halloween-ghost', 'pixel-car': 'halloween-car' };
  const resolved = state.theme === 'light' ? (lightAssets[name] || name) : name;
  return `/static/assets/${resolved}${state.motionPaused ? '-still' : ''}.svg`;
}
function seasonLabel() { return state.theme === 'light' ? 'PIXEL / HALLOWEEN' : 'PIXEL / WINTER'; }
function applyTheme(theme, persist = true) {
  state.theme = theme === 'light' ? 'light' : 'dark';
  clearWinterEggs();
  document.documentElement.dataset.theme = state.theme;
  if (persist) localStorage.setItem('its_theme', state.theme);
  document.querySelectorAll('[data-winter-art]').forEach(img => { img.src = themeAsset(img.dataset.winterArt); });
  document.querySelectorAll('.winter-label, .winter-caption').forEach(el => { el.textContent = seasonLabel(); });
  document.querySelectorAll('[data-theme-set]').forEach(btn => btn.setAttribute('aria-pressed', String(btn.dataset.themeSet === state.theme)));
  const toggle = $('#theme-toggle');
  const label = state.theme === 'light' ? 'Chuyển sang giao diện tối mùa đông' : 'Chuyển sang giao diện sáng Halloween';
  toggle.setAttribute('aria-label', label); toggle.title = label;
  toggle.innerHTML = icon(state.theme === 'light' ? 'moon' : 'sun');
  $('#motion-toggle').innerHTML = icon(state.theme === 'light' ? 'sparkle' : 'snow');
  $('#car-easter-hit').hidden = state.theme !== 'dark';
}
function initThemeControls() {
  applyTheme(state.theme, false);
  document.querySelectorAll('[data-theme-set]').forEach(btn => btn.addEventListener('click', () => applyTheme(btn.dataset.themeSet)));
  $('#theme-toggle').addEventListener('click', () => applyTheme(state.theme === 'light' ? 'dark' : 'light'));
}
function emptyState(name, title, description = '') { return `<div class="empty-state">${name === 'car' ? winterImage('winter-snowman', 'winter-mascot') : icon(name)}<strong>${esc(title)}</strong>${description ? `<p>${esc(description)}</p>` : ''}</div>`; }
function formatTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? esc(value) : esc(date.toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' }));
}
function canWrite() { return ['admin', 'operator'].includes(state.user && state.user.role); }
function updateReviewCount(count) {
  $('#review-badge').hidden = !count;
  $('#review-badge').textContent = count;
}
function syncIcons() { document.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = icon(el.dataset.icon); }); }

function toast(msg, tone = 'success') {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'toast ' + tone;
  t.hidden = false;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => (t.hidden = true), 3200);
}

async function api(path, opts = {}) {
  if (state.sessionExpired && path !== '/auth/login') throw new Error('Phiên đăng nhập đã hết hạn. Đăng nhập lại để tiếp tục; ảnh đã chọn vẫn được giữ.');
  const requestToken = state.token;
  const headers = { ...(opts.headers || {}) };
  if (state.token) headers['Authorization'] = 'Bearer ' + state.token;
  const signal = !opts.method || opts.method === 'GET' ? state.controller?.signal : undefined;
  let res;
  try { res = await fetch(path, { signal, ...opts, headers }); }
  catch (ex) {
    if (ex.name === 'AbortError') throw ex;
    throw new Error('Không kết nối được máy chủ. Kiểm tra kết nối rồi thử lại.');
  }
  let data = null;
  try { data = await res.json(); }
  catch (_) { if (res.ok) throw new Error('Máy chủ trả về dữ liệu không hợp lệ. Vui lòng thử lại.'); }
  if (res.ok && (!data || typeof data !== 'object')) throw new Error('Máy chủ trả về dữ liệu không hợp lệ. Vui lòng thử lại.');
  if (!res.ok) {
    if (res.status === 401) {
      if (path === '/auth/login') throw new Error('Tên đăng nhập hoặc mật khẩu không đúng.');
      if (requestToken === state.token || state.sessionExpired) requestReauthentication();
      throw new Error('Phiên đăng nhập đã hết hạn. Đăng nhập lại để tiếp tục; ảnh đã chọn vẫn được giữ.');
    }
    const msg = data && data.error ? data.error.message : (data && data.detail ? (typeof data.detail === 'string' ? data.detail : 'Lỗi') : 'Yêu cầu thất bại');
    throw new Error(msg);
  }
  return data;
}

function badge(label, tone) { return `<span class="badge ${tone}">${esc(label)}</span>`; }
function statusBadge(s) { const [l, t] = STATUS[s] || [s || 'Chờ xử lý', 'neutral']; return badge(l, t); }
function matchBadge(m) { const [l, t] = MATCH[m] || [m || 'Chờ đối chiếu', 'warning']; return badge(l, t); }

/* ====== LOGIN ====== */
function requestReauthentication() {
  if (!state.user || state.sessionExpired) return;
  state.sessionExpired = true; state.token = '';
  localStorage.removeItem(TOKEN_KEY);
  cameraClosers.forEach(close => close());
  $('#session-username').value = state.user.username;
  $('#session-password').value = '';
  $('#session-error').hidden = true;
  const dialog = $('#session-dialog');
  if (!dialog.open) dialog.showModal();
  $('#session-password').focus();
}
async function doSessionLogin(event) {
  event.preventDefault();
  const button = $('#session-submit'), error = $('#session-error');
  if (button.disabled) return;
  const original = button.innerHTML;
  button.disabled = true; button.innerHTML = '<span class="spinner"></span>Đang đăng nhập…'; error.hidden = true;
  try {
    const data = await api('/auth/login', { method: 'POST', body: new URLSearchParams({
      username: $('#session-username').value.trim(), password: $('#session-password').value,
    }) });
    if (typeof data.access_token !== 'string' || !data.access_token || !data.user || data.user.username !== $('#session-username').value.trim()) throw new Error('Phản hồi đăng nhập không hợp lệ. Vui lòng thử lại.');
    state.token = data.access_token; state.user = data.user; state.sessionExpired = false;
    localStorage.setItem(TOKEN_KEY, state.token);
    $('#session-dialog').close();
    document.querySelectorAll('[data-session-error]').forEach(result => { result.hidden = true; result.textContent = ''; delete result.dataset.sessionError; });
    syncUserShell();
    const entry = $('#entry-submit'), exit = $('#exit-submit');
    if (entry) entry.disabled = !canWrite();
    if (exit) exit.disabled = !canWrite() || !!$('#exit-ticket') && $('#exit-ticket').options.length <= 1;
    if (state.view === 'admin' && state.user.role !== 'admin') await showView('dashboard');
    toast('Đã đăng nhập lại. Bạn có thể tiếp tục thao tác với ảnh đã chọn.');
  } catch (ex) { error.textContent = ex.message; error.hidden = false; }
  finally { $('#session-password').value = ''; button.disabled = false; button.innerHTML = original; }
}
function setPasswordVisible(visible) {
  const input = $('#login-password');
  const start = input.selectionStart, end = input.selectionEnd;
  input.type = visible ? 'text' : 'password';
  if (start !== null && end !== null) input.setSelectionRange(start, end);
  $('#password-field').classList.toggle('lamp-on', visible);
  const button = $('#password-toggle');
  const label = visible ? 'Tắt đèn, ẩn mật khẩu' : 'Bật đèn, hiện mật khẩu';
  button.setAttribute('aria-pressed', String(visible));
  button.setAttribute('aria-label', label);
  button.title = label;
}
function initPasswordLamp() {
  $('#password-toggle').addEventListener('click', () => setPasswordVisible($('#login-password').type === 'password'));
}
async function doLogin(e) {
  e.preventDefault();
  const err = $('#login-error');
  err.hidden = true;
  try {
    const data = await api('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({
        username: $('#login-username').value.trim(),
        password: $('#login-password').value,
      }),
    });
    state.token = data.access_token;
    state.user = data.user;
    localStorage.setItem(TOKEN_KEY, state.token);
    $('#login-password').value = '';
    enterApp();
  } catch (ex) {
    err.textContent = ex.message;
    err.hidden = false;
  }
}

/* ====== APP SHELL ====== */
function enterApp() {
  state.sessionExpired = false;
  setPasswordVisible(false);
  clearWinterEggs();
  $('#login-view').hidden = true;
  $('#app-view').hidden = false;
  syncUserShell();
  showView('dashboard');
}
function syncUserShell() {
  $('#side-username').textContent = state.user.username;
  $('#side-role').textContent = ROLE[state.user.role] || state.user.role;
  $('#user-avatar').textContent = state.user.username.slice(0, 1).toUpperCase();
  $('#nav-admin').hidden = state.user.role !== 'admin';
}

function logout() {
  state.token = '';
  state.user = null;
  localStorage.removeItem(TOKEN_KEY);
  location.reload();
}

const VIEW_TITLES = {
  dashboard: 'Tổng quan',
  entry: 'Xe vào',
  exit: 'Xe ra',
  review: 'Cần kiểm tra',
  logs: 'Nhật ký nhận diện',
  admin: 'Quản lý tài khoản',
};

async function showView(name) {
  if (!RENDER[name]) return;
  previewCleanups.splice(0).forEach(cleanup => cleanup());
  state.controller?.abort();
  state.controller = new AbortController();
  state.view = name;
  const version = ++state.viewVersion;
  $('#view-title').textContent = VIEW_TITLES[name] || name;
  document.querySelectorAll('.nav-item').forEach((b) => {
    b.classList.toggle('active', b.dataset.view === name);
    if (b.dataset.view === name) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
  });
  const el = $('#view-content');
  el.innerHTML = '<div class="loading-state"><span class="spinner"></span>Đang tải dữ liệu…</div>';
  try {
    await RENDER[name]();
  } catch (ex) {
    if (version !== state.viewVersion || ex.name === 'AbortError') return;
    el.innerHTML = `<div class="card">${emptyState('review', 'Không tải được dữ liệu', ex.message)}<button class="btn btn-primary" id="retry-view">Thử lại</button></div>`;
    $('#retry-view').addEventListener('click', () => showView(name));
  }
}

/* ====== RENDERERS ====== */
const RENDER = {
  async dashboard() {
    const [summary, logs, active] = await Promise.all([
      api('/operations/summary'), api('/logs?limit=6'), api('/tickets/active'),
    ]);
    if (state.view !== 'dashboard') return;
    const k = summary.kpis || {}, items = logs.items || [];
    const reviewCount = k.review_tickets || 0;
    updateReviewCount(reviewCount);
    const cards = [
      ['car', 'blue', 'Đang trong bãi', k.active_tickets ?? 0],
      ['logs', 'purple', 'Tổng vé', k.total_tickets ?? 0],
      ['check', 'green', 'Đã hoàn tất', k.completed_tickets ?? 0],
      ['review', 'orange', 'Cần kiểm tra', reviewCount],
    ];
    const stats = cards.map(([name, tone, label, value]) => `<div class="card stat"><div class="stat-top"><span class="stat-label">${label}</span><span class="stat-icon ${tone}">${icon(name)}</span></div><div class="stat-value">${esc(value)}</div></div>`).join('');
    const health = summary.health || {};
    const healthLabel = { NORMAL: 'Bình thường', ATTENTION_REQUIRED: 'Cần kiểm tra', OCR_DEGRADED: 'Cần rà soát OCR' }[health.code] || 'Chưa xác định';
    const recentRows = items.map(r => `<tr><td class="ticket-id">${esc(r.ticket_id)}</td><td class="plate">${esc(r.plate_entry || r.plate_exit || '—')}</td><td>${statusBadge(r.status)}</td><td>${matchBadge(r.match_result)}</td><td class="time-cell">${formatTime(r.entry_time)}</td></tr>`).join('');
    const activeItems = active.items || [];
    $('#view-content').innerHTML = `
      <section class="winter-banner"><div class="banner-copy"><span class="winter-label">${seasonLabel()}</span><h2>Chào, ${esc(state.user.username)}</h2><p>${esc(new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'Asia/Ho_Chi_Minh' }))}</p></div><div class="winter-banner-art" aria-hidden="true">${winterImage('winter-scene')}</div><div class="banner-spark" aria-hidden="true"></div></section>
      <div class="grid grid-4 stats-grid">${stats}</div>
      <div class="quick-actions">
        ${canWrite() ? `<button class="quick-action" data-open="entry"><span class="action-icon blue">${icon('entry')}</span><span><strong>Ghi nhận xe vào</strong><small>Tạo vé từ ảnh biển số</small></span>${icon('entry')}</button><button class="quick-action" data-open="exit"><span class="action-icon purple">${icon('exit')}</span><span><strong>Ghi nhận xe ra</strong><small>Đối chiếu và hoàn tất vé</small></span>${icon('exit')}</button>` : `<button class="quick-action" data-open="logs"><span class="action-icon blue">${icon('logs')}</span><span><strong>Nhật ký lượt xe</strong><small>Tra cứu biển số và trạng thái vé</small></span>${icon('entry')}</button>`}
      </div>
      <div class="dashboard-grid">
        <section class="card activity-card"><div class="card-heading"><h3>Hoạt động gần đây</h3><button class="text-btn" data-open="logs">Xem tất cả ${icon('entry')}</button></div>
          ${items.length ? `<div class="table-wrap"><table><thead><tr><th>Mã vé</th><th>Biển số</th><th>Trạng thái</th><th>Đối chiếu</th><th>Thời gian vào</th></tr></thead><tbody>${recentRows}</tbody></table></div>` : emptyState('car', 'Chưa có lượt xe', 'Các lượt xe vào và ra sẽ xuất hiện tại đây.')}
        </section>
        <section class="card system-card"><div class="card-heading"><h3>Vận hành</h3><span class="status-dot ${health.tone === 'warning' ? 'warning' : ''}"></span></div>
          <div class="system-row"><span>Trạng thái</span>${badge(healthLabel, health.tone === 'warning' ? 'warning' : 'neutral')}</div>
          <div class="system-row"><span>Vé cần kiểm tra</span><strong>${esc(reviewCount)}</strong></div>
          <div class="system-row"><span>Lệch biển số</span><strong>${esc(k.mismatch_tickets || 0)}</strong></div>
          <button class="btn btn-soft btn-block" data-open="review">Xem vé cần kiểm tra ${icon('entry')}</button>
          <div class="updated-at">${icon('clock')}Cập nhật ${new Date().toLocaleTimeString('vi-VN')}</div>
        </section>
      </div>
      ${activeItems.length ? `<section class="card active-card"><div class="card-heading"><h3>Vé đang mở</h3><span class="count-chip">${activeItems.length}</span></div><div class="table-wrap"><table><thead><tr><th>Mã vé</th><th>Biển số</th><th>Trạng thái</th><th>Thời gian vào</th></tr></thead><tbody>${activeItems.map(r => `<tr><td class="ticket-id">${esc(r.ticket_id)}</td><td class="plate">${esc(r.plate_entry || '—')}</td><td>${statusBadge(r.status)}</td><td>${formatTime(r.entry_time)}</td></tr>`).join('')}</tbody></table></div></section>` : ''}`;
    document.querySelectorAll('[data-open]').forEach(btn => btn.addEventListener('click', () => showView(btn.dataset.open)));
  },

  async entry() {
    $('#view-content').innerHTML = `
      <div class="workflow-grid">
        <section class="card upload-card"><div class="card-heading"><h3>Ảnh biển số xe vào</h3><span class="step-chip">01</span></div>${uploadMarkup('entry')}</section>
        <section class="card details-card"><div class="card-heading"><h3>Thông tin vé & Quẹt thẻ RFID</h3><span class="step-chip">02</span></div>
          <div class="form-row vertical">
            <label>Mã thẻ RFID / Chip NFC
              <input id="entry-card" placeholder="Quẹt thẻ USB hoặc chạm NFC lưng điện thoại..." autofocus />
            </label>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 10px">
              <button type="button" class="btn btn-sm btn-soft" id="btn-nfc-entry">📱 Chạm thẻ NFC điện thoại</button>
              <button type="button" class="btn btn-sm btn-soft" id="btn-preset-sv">Thẻ SV mẫu (59X3-123.45)</button>
              <button type="button" class="btn btn-sm btn-soft" id="btn-preset-staff">Thẻ Giảng viên (0đ Miễn phí)</button>
            </div>
            <label>Đối tượng gửi xe
              <select id="entry-user-type">
                <option value="STUDENT">Sinh viên (5.000đ - Tự động ưu tiên B -> C -> A)</option>
                <option value="STAFF">Cán bộ / Giảng viên (0đ Miễn phí - Khu E Tầng dưới)</option>
                <option value="GUEST">Khách liên hệ (5.000đ)</option>
              </select>
            </label>
            <label>Biển số xe <span class="optional">· tùy chọn</span><input id="entry-plate" placeholder="59X3-123.45" /></label>
          </div>
          <p class="field-help">Có thể quẹt đầu đọc thẻ USB, chạm NFC điện thoại, hoặc bấm Thẻ SV mẫu để thử nghiệm ngay.</p>
          <button class="btn btn-primary btn-block" id="entry-submit" ${canWrite() ? '' : 'disabled'}>${icon('entry')}Tạo vé xe vào</button>
        </section>
      </div><div id="entry-result" class="operation-result" role="status"></div>`;

    const upload = bindUpload('entry');

    $('#btn-preset-sv').addEventListener('click', () => {
      $('#entry-card').value = 'UTH_SV_2026_01';
      $('#entry-plate').value = '59X3-123.45';
      $('#entry-user-type').value = 'STUDENT';
      toast('Đã nạp Thẻ Sinh viên mẫu');
    });

    $('#btn-preset-staff').addEventListener('click', () => {
      $('#entry-card').value = 'UTH_STAFF_GV_01';
      $('#entry-plate').value = '51F-888.88';
      $('#entry-user-type').value = 'STAFF';
      toast('Đã nạp Thẻ Giảng viên mẫu (Miễn phí 0đ)');
    });

    $('#btn-nfc-entry').addEventListener('click', async () => {
      if (!('NDEFReader' in window)) {
        toast('Trình duyệt chưa hỗ trợ Web NFC. Hãy dùng Chrome trên Android có bật NFC hoặc dùng phím/thẻ mẫu nhé!', 'warning');
        return;
      }
      try {
        toast('Đang sẵn sàng! Hãy áp thẻ sinh viên vào lưng điện thoại...', 'info');
        const ndef = new NDEFReader();
        await ndef.scan();
        ndef.onreading = (event) => {
          const serial = (event.serialNumber || 'NFC_' + Date.now().toString(16)).toUpperCase();
          $('#entry-card').value = serial;
          toast(`Đã nhận diện thẻ NFC: ${serial}`, 'success');
        };
      } catch (err) {
        toast('Lỗi NFC: ' + (err.message || err), 'error');
      }
    });

    $('#entry-submit').addEventListener('click', async () => {
      if (!canWrite()) return;
      let f = upload.getFile();
      const plateText = $('#entry-plate').value.trim();
      const cardId = $('#entry-card').value.trim();
      const userType = $('#entry-user-type').value;

      if (!f) {
        const canvas = document.createElement('canvas');
        canvas.width = 320; canvas.height = 140;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 320, 140);
        ctx.strokeStyle = '#0f172a'; ctx.lineWidth = 4; ctx.strokeRect(6, 6, 308, 128);
        ctx.fillStyle = '#0f172a'; ctx.font = 'bold 36px monospace';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(plateText || '59X3-123.45', 160, 70);
        f = await new Promise(res => canvas.toBlob(b => res(new File([b], 'plate.jpg', { type: 'image/jpeg' })), 'image/jpeg'));
      }

      const fd = new FormData();
      fd.append('file', f);
      if (plateText) fd.append('plate_text', plateText);
      if (cardId) fd.append('card_id', cardId);
      fd.append('user_type', userType);

      const btn = $('#entry-submit'), version = state.viewVersion;
      await runPending(btn, 'Đang tạo vé…', async () => {
        const data = await api('/vehicle/entry', { method: 'POST', body: fd });
        if (version !== state.viewVersion) return;
        const r = data.result || {};
        $('#entry-result').innerHTML = `
          <div class="card result-card">
            <div class="result-icon">${icon('check')}</div>
            <div>
              <h3>Đã tạo vé ${esc(r.ticket_id)}</h3>
              <span class="plate">${esc(r.plate_entry || '—')}</span> · 
              <strong>${esc(r.zone_assigned ? 'Phân bổ: ' + r.zone_assigned : '')}</strong>
              <div style="margin-top:6px;font-size:13px;color:var(--muted)">Mã thẻ: <code>${esc(r.card_id || 'Không có')}</code> | Đối tượng: <strong>${esc(r.user_type || userType)}</strong> | Phí: <strong>${(r.fee || 0).toLocaleString()} VND</strong></div>
              <div style="margin-top:6px">${r.review_required ? badge('Cần đối chiếu ảnh', 'warning') : statusBadge(r.status || 'IN_PARKING')}</div>
            </div>
          </div>`;
        toast('Đã tạo vé xe vào thành công');
        upload.reset();
        $('#entry-plate').value = '';
        $('#entry-card').value = '';
      });
    });
  },

  async exit() {
    const active = await api('/tickets/active');
    if (state.view !== 'exit') return;
    const items = (active.items || []).filter(t => t.status === 'IN_PARKING');
    $('#view-content').innerHTML = `
      <div class="workflow-grid">
        <section class="card upload-card"><div class="card-heading"><h3>Ảnh biển số xe ra</h3><span class="step-chip">01</span></div>${uploadMarkup('exit')}</section>
        <section class="card details-card"><div class="card-heading"><h3>Đối chiếu vé & Quẹt thẻ ra</h3><span class="step-chip">02</span></div>
          <div class="form-row vertical">
            <label>Quẹt thẻ RFID / Chip NFC ra
              <input id="exit-card" placeholder="Quẹt thẻ hoặc chọn vé bên dưới..." autofocus />
            </label>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 10px">
              <button type="button" class="btn btn-sm btn-soft" id="btn-nfc-exit">📱 Chạm thẻ NFC điện thoại</button>
              <button type="button" class="btn btn-sm btn-soft" id="btn-preset-sv-exit">Thẻ SV mẫu</button>
              <button type="button" class="btn btn-sm btn-soft" id="btn-preset-staff-exit">Thẻ Giảng viên (0đ)</button>
            </div>
            <label>Vé đang trong bãi
              <select id="exit-ticket">
                <option value="">${items.length ? 'Chọn vé (hoặc quẹt thẻ ở trên)' : 'Chưa có vé đang trong bãi'}</option>
                ${items.map(t => `<option value="${esc(t.ticket_id)}" data-card="${esc(t.card_id || '')}" data-plate="${esc(t.plate_entry || '')}">${esc(t.plate_entry)} · ${esc(t.ticket_id)} (${esc(t.card_id || 'Không thẻ')})</option>`).join('')}
              </select>
            </label>
            <label>Hình thức thanh toán
              <select id="exit-payment-method">
                <option value="VIETQR">Mã VietQR Động (Napas 247)</option>
                <option value="CASH">Tiền mặt</option>
              </select>
            </label>
            <label>Biển số nhập tay <span class="optional">· tùy chọn</span><input id="exit-plate" placeholder="59X3-123.45" /></label>
          </div>
          <p class="field-help">Quẹt thẻ sẽ tự động chọn vé và đồng bộ hiển thị mã VietQR trên màn hình phụ.</p>
          <button class="btn btn-primary btn-block" id="exit-submit" ${canWrite() && items.length ? '' : 'disabled'}>${icon('exit')}Xác nhận xe ra & Mở Barrier</button>
        </section>
      </div><div id="exit-result" class="operation-result" role="status"></div>`;

    const upload = bindUpload('exit');

    // Tự động tìm vé theo mã thẻ
    const matchCardToTicket = (cardVal) => {
      const clean = (cardVal || '').trim().toUpperCase();
      if (!clean) return;
      const opts = [...$('#exit-ticket').options];
      const match = opts.find(o => (o.dataset.card || '').toUpperCase() === clean);
      if (match) {
        $('#exit-ticket').value = match.value;
        if (match.dataset.plate) $('#exit-plate').value = match.dataset.plate;
        toast(`Đã khớp vé: ${match.value}`);
      }
    };

    $('#exit-card').addEventListener('input', (e) => matchCardToTicket(e.target.value));

    $('#btn-preset-sv-exit').addEventListener('click', () => {
      $('#exit-card').value = 'UTH_SV_2026_01';
      matchCardToTicket('UTH_SV_2026_01');
      if (!$('#exit-plate').value) $('#exit-plate').value = '59X3-123.45';
    });

    $('#btn-preset-staff-exit').addEventListener('click', () => {
      $('#exit-card').value = 'UTH_STAFF_GV_01';
      matchCardToTicket('UTH_STAFF_GV_01');
      if (!$('#exit-plate').value) $('#exit-plate').value = '51F-888.88';
    });

    $('#btn-nfc-exit').addEventListener('click', async () => {
      if (!('NDEFReader' in window)) {
        toast('Trình duyệt chưa hỗ trợ Web NFC. Hãy dùng Chrome trên Android có bật NFC nhé!', 'warning');
        return;
      }
      try {
        toast('Đang sẵn sàng! Hãy áp thẻ vào lưng điện thoại...', 'info');
        const ndef = new NDEFReader();
        await ndef.scan();
        ndef.onreading = (event) => {
          const serial = (event.serialNumber || 'NFC_' + Date.now().toString(16)).toUpperCase();
          $('#exit-card').value = serial;
          matchCardToTicket(serial);
          toast(`Đã nhận diện thẻ NFC: ${serial}`, 'success');
        };
      } catch (err) {
        toast('Lỗi NFC: ' + (err.message || err), 'error');
      }
    });

    $('#exit-ticket').addEventListener('change', () => {
      const sel = $('#exit-ticket').selectedOptions[0];
      if (sel && sel.dataset.plate) {
        $('#exit-plate').value = sel.dataset.plate;
        if (sel.dataset.card) $('#exit-card').value = sel.dataset.card;
      }
    });

    $('#exit-submit').addEventListener('click', async () => {
      if (!canWrite()) return;
      const tid = $('#exit-ticket').value;
      const cardId = $('#exit-card').value.trim();
      const paymentMethod = $('#exit-payment-method').value;
      const plateText = $('#exit-plate').value.trim();

      if (!tid && !cardId) { toast('Vui lòng chọn vé hoặc quẹt thẻ', 'error'); return; }

      let f = upload.getFile();
      if (!f) {
        const canvas = document.createElement('canvas');
        canvas.width = 320; canvas.height = 140;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 320, 140);
        ctx.strokeStyle = '#0f172a'; ctx.lineWidth = 4; ctx.strokeRect(6, 6, 308, 128);
        ctx.fillStyle = '#0f172a'; ctx.font = 'bold 36px monospace';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(plateText || '59X3-123.45', 160, 70);
        f = await new Promise(res => canvas.toBlob(b => res(new File([b], 'plate_exit.jpg', { type: 'image/jpeg' })), 'image/jpeg'));
      }

      const fd = new FormData();
      if (tid) fd.append('ticket_id', tid);
      if (cardId) fd.append('card_id', cardId);
      fd.append('file', f);
      if (plateText) fd.append('plate_text', plateText);
      fd.append('payment_method', paymentMethod);

      const btn = $('#exit-submit'), version = state.viewVersion;
      await runPending(btn, 'Đang đối chiếu…', async () => {
        const data = await api('/vehicle/exit', { method: 'POST', body: fd });
        if (version !== state.viewVersion) return;
        const r = data.result || {};
        const isStaff = r.user_type === 'STAFF' || r.fee === 0;

        let qrMarkup = '';
        if (r.vietqr && r.vietqr.qr_image_url && !isStaff) {
          qrMarkup = `
            <div style="margin-top:12px;padding:12px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;text-align:center">
              <div style="font-weight:600;margin-bottom:8px">Quét mã VietQR Napas 247 thanh toán ${(r.fee || 5000).toLocaleString()} VND:</div>
              <img src="${esc(r.vietqr.qr_image_url)}" alt="VietQR" style="max-width:240px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.08)" />
              <div style="margin-top:8px;font-size:12px;color:var(--muted)">Đồng bộ thời gian thực với Màn hình phụ trên điện thoại khách hàng</div>
            </div>`;
        }

        $('#exit-result').innerHTML = `
          <div class="card result-card">
            <div>
              <h3>Đã ghi nhận xe ra · ${isStaff ? 'MIỄN PHÍ 0đ (CB-GV)' : 'PHÍ: ' + (r.fee || 5000).toLocaleString() + ' VND'}</h3>
              <span class="plate">${esc(r.plate_exit || '—')}</span> ${matchBadge(r.match_result)} ${statusBadge(r.status)}
              <div style="margin-top:6px;font-size:13px;color:var(--muted)">
                Mã vé: <strong>${esc(r.ticket_id || tid)}</strong> | Thẻ: <code>${esc(r.card_id || cardId || '—')}</code> | 
                ${isStaff ? '<span style="color:#16a34a;font-weight:700">BARRIER ĐÃ TỰ ĐỘNG MỞ</span>' : 'Hình thức: ' + esc(r.payment_method || paymentMethod)}
              </div>
              ${qrMarkup}
            </div>
          </div>`;

        toast('Đã ghi nhận xe ra');
        upload.reset();
        const option = [...$('#exit-ticket').options].find(o => o.value === (r.ticket_id || tid));
        if (option && r.status && r.status !== 'IN_PARKING') option.remove();
        $('#exit-ticket').value = '';
        $('#exit-plate').value = '';
        $('#exit-card').value = '';
        if ($('#exit-ticket').options.length <= 1) {
          btn.dataset.keepDisabled = 'true';
          $('#exit-ticket').options[0].textContent = 'Chưa có vé đang trong bãi';
        }
      });
    });
  },

  async review() {
    const logs = await api('/logs?status=NEEDS_REVIEW&limit=200');
    if (state.view !== 'review') return;
    const items = logs.items || [];
    updateReviewCount(logs.total ?? items.length);
    $('#view-content').innerHTML = items.length ? `
      <div class="grid" style="grid-template-columns:1fr">${items.map((r) => `
        <div class="card" data-ticket="${esc(r.ticket_id)}">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <h3 style="margin:0">Vé ${esc(r.ticket_id)}</h3>
            <span>${matchBadge(r.match_result)}</span>
          </div>
          <div class="grid grid-2" style="margin:12px 0">
            <div>Biển vào: <span class="plate">${esc(r.plate_entry || '—')}</span></div>
            <div>Biển ra: <span class="plate">${esc(r.plate_exit || '—')}</span></div>
          </div>
          <div style="color:var(--muted);font-size:13px">Lý do: ${esc(r.review_reason || '')}</div>
          ${canWrite() ? `<div class="row-actions" style="margin-top:18px">
            <button class="btn btn-success btn-sm" data-action="APPROVE_EXIT">Duyệt ra</button>
            <button class="btn btn-primary btn-sm" data-action="MARK_MATCH">Đánh dấu khớp</button>
            <button class="btn btn-warning btn-sm" data-action="REJECT_EXIT">Từ chối</button>
            ${state.user.role === 'admin' ? '<button class="btn btn-danger btn-sm" data-action="CANCEL">Hủy vé</button>' : ''}
          </div>` : ''}
        </div>`).join('')}</div>` : `<div class="card">${emptyState('check', 'Không có vé cần kiểm tra', 'Các vé cần đối chiếu sẽ xuất hiện tại đây.')}</div>`;

    document.querySelectorAll('[data-action]').forEach((btn) => btn.addEventListener('click', async () => {
      const ticket = btn.closest('[data-ticket]').dataset.ticket;
      const action = btn.dataset.action;
      if (!canWrite()) return;
      let reason = '';
      if (action === 'CANCEL') {
        reason = prompt('Lý do hủy vé:')?.trim() || '';
        if (!reason) return;
      }
      await runPending(btn, 'Đang xử lý…', async () => {
        if (action === 'CANCEL') {
          await api(`/tickets/${encodeURIComponent(ticket)}/cancel`, { method: 'POST', body: new URLSearchParams({ reason }) });
        } else {
          await api(`/tickets/${encodeURIComponent(ticket)}/resolve`, { method: 'POST', body: new URLSearchParams({ resolution: action, note: '' }) });
        }
        toast('Đã xử lý');
        if (state.view === 'review') await showView('review');
      });
    }));
  },

  async logs() {
    const logs = await api('/logs?limit=500');
    if (state.view !== 'logs') return;
    const items = logs.items || [];
    $('#view-content').innerHTML = `
      <div class="card">
        <div class="card-heading"><h3>Nhật ký lượt xe</h3><span class="count-chip">${items.length} / ${esc(logs.total ?? items.length)} vé</span></div>
        <div class="form-row" style="margin-bottom:14px">
          <label>Lọc trạng thái
            <select id="log-filter">
              <option value="">Tất cả</option>
              <option value="IN_PARKING">Đang trong bãi</option>
              <option value="NEEDS_REVIEW">Cần kiểm tra</option>
              <option value="COMPLETED">Đã hoàn tất</option>
              <option value="CANCELLED">Đã hủy</option>
            </select>
          </label>
          <label>Tìm kiếm<input id="log-search" placeholder="Biển số vào, ra hoặc mã vé" type="search" /></label>
        </div>
        <div class="table-wrap"><table>
          <thead><tr><th>Vé</th><th>Biển vào</th><th>Biển ra</th><th>Trạng thái</th><th>Đối chiếu</th><th>Thời gian vào</th></tr></thead>
          <tbody id="log-tbody"></tbody>
        </table></div>
      </div>`;

    const render = (list) => {
      $('#log-tbody').innerHTML = list.map((r) => `
        <tr><td>${esc(r.ticket_id)}</td><td class="plate">${esc(r.plate_entry || '—')}</td><td class="plate">${esc(r.plate_exit || '—')}</td>
        <td>${statusBadge(r.status)}</td><td>${matchBadge(r.match_result)}</td><td class="time-cell">${formatTime(r.entry_time)}</td></tr>`).join('') || `<tr><td colspan="6">${emptyState('search', 'Không tìm thấy vé')}</td></tr>`;
    };
    render(items);

    const filter = () => {
      const st = $('#log-filter').value.toLowerCase();
      const q = $('#log-search').value.toLowerCase();
      render(items.filter((r) => (!st || (r.status || '').toLowerCase() === st) && (!q || [r.plate_entry, r.plate_exit, r.ticket_id].some(value => String(value || '').toLowerCase().includes(q)))));
    };
    $('#log-filter').addEventListener('change', filter);
    $('#log-search').addEventListener('input', filter);
  },

  async admin() {
    const users = await api('/admin/users');
    if (state.view !== 'admin') return;
    const items = users.items || [];
    $('#view-content').innerHTML = `
      <div class="card">
        <h3>Tạo tài khoản</h3>
        <div class="form-row">
          <label>Tên đăng nhập<input id="u-username" /></label>
          <label>Mật khẩu<input id="u-password" type="password" /></label>
          <label>Vai trò
            <select id="u-role">${Object.entries(ROLE).reverse().map(([role, label]) => `<option value="${role}">${label}</option>`).join('')}</select>
          </label>
        </div>
        <button class="btn btn-primary" id="u-create">${icon('users')}Tạo tài khoản</button>
      </div>
      <div class="card" style="margin-top:16px">
        <h3>Danh sách tài khoản</h3>
        <div class="table-wrap"><table>
          <thead><tr><th>Tên đăng nhập</th><th>Vai trò</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
          <tbody id="u-tbody"></tbody>
        </table></div>
      </div>`;

    const render = () => {
      $('#u-tbody').innerHTML = items.map((u) => `
        <tr><td class="ticket-id">${esc(u.username)}</td><td><select class="role-select" aria-label="Vai trò của ${esc(u.username)}" data-role-user="${esc(u.username)}">${Object.entries(ROLE).map(([role, label]) => `<option value="${role}" ${u.role === role ? 'selected' : ''}>${label}</option>`).join('')}</select></td>
        <td>${badge(u.is_active ? 'Hoạt động' : 'Khóa', u.is_active ? 'success' : 'neutral')}</td>
        <td><div class="row-actions">
          <button class="btn btn-sm btn-soft" data-u="${esc(u.username)}" data-op="role">Lưu vai trò</button>
          <button class="btn btn-sm ${u.is_active ? 'btn-warning' : 'btn-success'}" data-u="${esc(u.username)}" data-op="active" ${u.username === state.user.username ? 'disabled' : ''}>${u.is_active ? 'Khóa' : 'Mở khóa'}</button>
          <button class="btn btn-sm btn-danger" data-u="${esc(u.username)}" data-op="delete" ${u.username === state.user.username ? 'disabled' : ''}>Xóa</button>
        </div></td></tr>`).join('') || '<tr><td colspan="4" class="empty">Chưa có tài khoản</td></tr>';
    };
    render();

    $('#u-create').addEventListener('click', async () => {
      const username = $('#u-username').value.trim(), password = $('#u-password').value, role = $('#u-role').value;
      if (!username || !password) { toast('Nhập tên đăng nhập và mật khẩu', 'error'); return; }
      await runPending($('#u-create'), 'Đang tạo…', async () => {
        await api('/admin/users', { method: 'POST', body: new URLSearchParams({ username, password, role }) });
        toast('Đã tạo tài khoản');
        if (state.view === 'admin') await showView('admin');
      });
    });

    document.querySelectorAll('[data-op]').forEach((btn) => btn.addEventListener('click', async () => {
      const u = btn.dataset.u, op = btn.dataset.op;
      const account = items.find(item => item.username === u);
      const selectedRole = [...document.querySelectorAll('[data-role-user]')].find(el => el.dataset.roleUser === u)?.value;
      if (op === 'delete' && !confirm(`Xóa tài khoản ${u}?`)) return;
      await runPending(btn, 'Đang lưu…', async () => {
        if (op === 'delete') {
          await api(`/admin/users/${encodeURIComponent(u)}`, { method: 'DELETE' });
        } else if (op === 'role') {
          await api(`/admin/users/${encodeURIComponent(u)}/role`, { method: 'PATCH', body: new URLSearchParams({ role: selectedRole }) });
        } else if (op === 'active') {
          await api(`/admin/users/${encodeURIComponent(u)}/active`, { method: 'PATCH', body: new URLSearchParams({ is_active: String(!account.is_active) }) });
        }
        toast('Đã cập nhật');
        if (state.view === 'admin') await showView('admin');
      });
    }));
  },
};

function uploadMarkup(prefix) {
  return `<button type="button" class="drop-zone" id="${prefix}-drop">${icon('upload')}<strong>Chọn ảnh biển số</strong><span>Hoặc kéo thả ảnh vào đây</span><small>JPG, PNG, WEBP · Tối đa 10 MB</small></button><input type="file" id="${prefix}-file" accept=".jpg,.jpeg,.png,.webp" hidden />
    <div class="preview" id="${prefix}-preview"></div><div class="file-meta" id="${prefix}-meta" hidden><span id="${prefix}-filename"></span><button class="text-btn" type="button" id="${prefix}-remove">Bỏ ảnh</button></div>
    <div class="camera-actions"><button type="button" class="btn btn-soft" id="${prefix}-camera-open">${icon('camera')}Mở camera</button><button type="button" class="btn btn-soft" id="${prefix}-camera-phone">${icon('camera')}Camera điện thoại</button></div>
    <input type="file" id="${prefix}-camera-native" accept="image/jpeg,image/png,image/webp" capture="environment" hidden />
    <div class="camera-panel" id="${prefix}-camera-panel" hidden>
      <label>Chọn camera<select id="${prefix}-camera-devices"><option value="">Camera mặc định</option></select></label>
      <div class="camera-feed"><video id="${prefix}-camera-video" autoplay muted playsinline></video><div class="camera-guide" aria-hidden="true"></div></div>
      <p class="camera-message" id="${prefix}-camera-message" role="status"></p><p class="camera-tip">Đưa biển số vào khung, giữ máy đứng yên và tránh ánh sáng phản chiếu.</p>
      <div class="camera-actions"><button type="button" class="btn btn-primary" id="${prefix}-camera-shutter" disabled>${icon('camera')}Chụp ảnh</button><button type="button" class="btn btn-soft" id="${prefix}-camera-close">Đóng camera</button></div>
    </div>
    <button type="button" class="btn btn-soft btn-block camera-scan" id="${prefix}-scan" hidden>${icon('search')}Quét biển số</button><div id="${prefix}-scan-result" class="camera-scan-result" role="status" hidden></div>`;
}

const previewCleanups = [];
const cameraClosers = new Set();

const winterEggs = { clicks: 0, lastClick: 0, turboTimer: null, friendTimer: null };
function clearWinterEggs() {
  clearTimeout(winterEggs.turboTimer); clearTimeout(winterEggs.friendTimer);
  winterEggs.clicks = 0;
  $('#login-view').classList.remove('winter-turbo');
  $('#winter-secret').hidden = true;
  $('#winter-aurora').hidden = true;
  $('#winter-egg-status').textContent = '';
}
function initWinterEasterEggs() {
  $('.turbo-snow').innerHTML = Array.from({ length: 14 }, (_, i) => `<i style="--spray-y:${(i % 7 - 3) * 14}px;--spray-delay:${i * .09}s;--spray-size:${3 + i % 3 * 2}px"></i>`).join('');
  $('#car-easter-hit').addEventListener('click', () => {
    if (state.theme !== 'dark' || $('#login-view').classList.contains('winter-turbo')) return;
    $('#login-view').classList.add('winter-turbo');
    $('#winter-egg-status').textContent = 'Turbo mùa đông đã bật!';
    winterEggs.turboTimer = setTimeout(() => {
      $('#login-view').classList.remove('winter-turbo');
      $('#winter-egg-status').textContent = '';
    }, 3000);
  });
  document.querySelectorAll('.winter-secret-logo').forEach(logo => logo.addEventListener('click', () => {
    if (state.theme !== 'dark') return;
    const now = Date.now();
    winterEggs.clicks = now - winterEggs.lastClick < 1800 ? winterEggs.clicks + 1 : 1;
    winterEggs.lastClick = now;
    if (winterEggs.clicks < 3) return;
    winterEggs.clicks = 0;
    clearTimeout(winterEggs.friendTimer);
    $('#winter-secret').hidden = false;
    $('#winter-aurora').hidden = false;
    winterEggs.friendTimer = setTimeout(() => {
      $('#winter-secret').hidden = true; $('#winter-aurora').hidden = true;
    }, 8000);
  }));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') clearWinterEggs(); });
}

function initWinterEffects() {
  document.querySelectorAll('.snowfield').forEach(field => {
    field.innerHTML = Array.from({ length: 30 }, (_, i) => `<i style="--x:${(i * 37 + 11) % 100}%;--drift:${(i % 5 - 2) * 28}px;--duration:${12 + i % 13}s;--delay:-${i * 2.3}s;--size:${i % 3 + 2}px;--alpha:${.2 + i % 4 * .12}"></i>`).join('');
  });
  const button = $('#motion-toggle');
  const applyMotion = paused => {
    state.motionPaused = paused;
    document.body.classList.toggle('motion-paused', paused);
    document.querySelectorAll('[data-winter-art]').forEach(img => { img.src = themeAsset(img.dataset.winterArt); });
    button.setAttribute('aria-pressed', String(paused));
    button.setAttribute('aria-label', paused ? 'Bật chuyển động' : 'Giảm chuyển động');
    button.title = paused ? 'Bật chuyển động' : 'Giảm chuyển động';
  };
  const preference = localStorage.getItem('its_reduce_motion');
  applyMotion(preference === 'true' || (preference === null && window.matchMedia('(prefers-reduced-motion: reduce)').matches));
  button.addEventListener('click', () => {
    applyMotion(!state.motionPaused);
    localStorage.setItem('its_reduce_motion', String(state.motionPaused));
  });
}
function bindUpload(prefix) {
  const drop = $(`#${prefix}-drop`), input = $(`#${prefix}-file`);
  const preview = $(`#${prefix}-preview`), meta = $(`#${prefix}-meta`);
  const scanButton = $(`#${prefix}-scan`), scanResult = $(`#${prefix}-scan-result`);
  let selectedFile = null, previewUrl = '', scanController = null, scanVersion = 0, disposed = false;
  const scanLabel = `${icon('search')}Quét biển số`;
  const resetScan = () => {
    scanController?.abort(); scanVersion++;
    scanButton.disabled = false; scanButton.innerHTML = scanLabel;
    scanResult.hidden = true; scanResult.innerHTML = '';
    delete scanResult.dataset.sessionError;
  };
  const reset = () => {
    camera.close(); resetScan(); scanButton.hidden = true;
    selectedFile = null; input.value = ''; preview.innerHTML = ''; meta.hidden = true; drop.hidden = false;
    if (previewUrl) { URL.revokeObjectURL(previewUrl); previewUrl = ''; }
  };
  const select = (file) => {
    if (!file) return false;
    if (!/\.(jpe?g|png|webp)$/i.test(file.name) || (file.type && !['image/jpeg', 'image/png', 'image/webp'].includes(file.type))) {
      input.value = ''; toast('Vui lòng chọn ảnh JPG, PNG hoặc WEBP', 'error'); return false;
    }
    if (!file.size || file.size > 10 * 1024 * 1024) {
      input.value = ''; toast(file.size ? 'Ảnh vượt quá 10 MB. Vui lòng chọn ảnh nhỏ hơn.' : 'Tệp ảnh trống. Vui lòng chọn ảnh khác.', 'error'); return false;
    }
    camera.close();
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    selectedFile = file; previewUrl = URL.createObjectURL(file);
    preview.innerHTML = `<img src="${esc(previewUrl)}" alt="Ảnh biển số đã chọn" />`;
    $(`#${prefix}-filename`).textContent = file.name;
    meta.hidden = false; drop.hidden = true;
    resetScan(); scanButton.hidden = false;
    return true;
  };
  const camera = bindCameraCapture(prefix, select, active => {
    drop.hidden = active || !!selectedFile; preview.hidden = active;
    meta.hidden = active || !selectedFile; scanButton.hidden = active || !selectedFile;
  });
  cameraClosers.add(camera.close);
  scanButton.addEventListener('click', async () => {
    if (!selectedFile || disposed || scanButton.disabled) return;
    const file = selectedFile, version = state.viewVersion, request = ++scanVersion;
    scanController?.abort(); scanController = new AbortController();
    const body = new FormData(); body.append('file', file);
    scanButton.disabled = true; scanButton.innerHTML = '<span class="spinner"></span>Đang quét biển số…';
    scanResult.hidden = true;
    try {
      const data = await api('/ocr', { method: 'POST', body, signal: scanController.signal });
      if (disposed || request !== scanVersion || version !== state.viewVersion || file !== selectedFile) return;
      const ocr = data.ocr || {}, plate = (ocr.text || '').trim();
      scanResult.innerHTML = plate ? `<span class="plate">${esc(plate)}</span> ${badge('Cần đối chiếu ảnh', 'warning')}<p>Kiểm tra biển số với ảnh trước khi ghi nhận lượt xe.</p>` : '<p>Chưa đọc được biển số. Chụp lại ảnh rõ hơn hoặc nhập tay sau khi đối chiếu.</p>';
      scanResult.hidden = false;
    } catch (error) {
      if (!disposed && request === scanVersion && version === state.viewVersion && error.name !== 'AbortError') {
        scanResult.textContent = error.message; scanResult.hidden = false;
        if (state.sessionExpired) scanResult.dataset.sessionError = 'true';
      }
    } finally {
      if (!disposed && request === scanVersion) { scanButton.disabled = false; scanButton.innerHTML = scanLabel; }
    }
  });
  drop.addEventListener('click', () => input.click());
  input.addEventListener('change', () => select(input.files[0]));
  const zone = drop.closest('.upload-card');
  zone.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('drag'); });
  zone.addEventListener('dragleave', () => drop.classList.remove('drag'));
  zone.addEventListener('drop', e => { e.preventDefault(); drop.classList.remove('drag'); select(e.dataTransfer.files[0]); });
  $(`#${prefix}-remove`).addEventListener('click', reset);
  previewCleanups.push(() => {
    disposed = true; scanController?.abort(); camera.dispose();
    cameraClosers.delete(camera.close);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  });
  return { getFile: () => selectedFile, reset };
}

async function runPending(btn, label, action) {
  if (btn.disabled) return;
  const original = btn.innerHTML;
  btn.disabled = true; btn.innerHTML = `<span class="spinner"></span>${esc(label)}`;
  try { await action(); } catch (ex) { toast(ex.message, 'error'); }
  finally { btn.disabled = btn.dataset.keepDisabled === 'true'; btn.innerHTML = original; }
}

/* ====== INIT ====== */
document.addEventListener('DOMContentLoaded', async () => {
  syncIcons();
  initThemeControls();
  initPasswordLamp();
  initWinterEffects();
  initWinterEasterEggs();
  $('#refresh-btn').addEventListener('click', () => showView(state.view));
  const tickClock = () => { $('#clock').textContent = new Date().toLocaleTimeString('vi-VN'); };
  tickClock();
  setInterval(tickClock, 1000);

  $('#login-form').addEventListener('submit', doLogin);
  $('#session-form').addEventListener('submit', doSessionLogin);
  $('#session-dialog').addEventListener('cancel', event => { if (state.sessionExpired) event.preventDefault(); });
  $('#logout-btn').addEventListener('click', logout);
  document.querySelectorAll('.nav-item').forEach((b) => b.addEventListener('click', () => showView(b.dataset.view)));

  if (state.token) {
    try {
      const me = await api('/auth/me');
      state.user = me.user;
      enterApp();
      return;
    } catch (_) { localStorage.removeItem(TOKEN_KEY); state.token = ''; }
  }
  $('#login-view').hidden = false;
});
