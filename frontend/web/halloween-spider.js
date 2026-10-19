'use strict';

document.addEventListener('DOMContentLoaded', () => {
  const spider = document.querySelector('#halloween-spider');
  const hug = document.querySelector('#spider-hug');
  const status = document.querySelector('#spider-status');
  const art = `<svg viewBox="0 0 96 96" fill="none" shape-rendering="crispEdges" aria-hidden="true">
    <g stroke="#604363" stroke-width="5" stroke-linejoin="round">
      <path class="spider-leg-a" d="M35 40 24 30 10 18 6 7M33 52 21 58 8 74 8 86M62 46 76 40 88 36 92 22M60 58 73 67 82 84 91 89"/>
      <path class="spider-leg-b" d="M34 46 20 40 8 36 4 22M36 58 23 67 14 84 5 89M61 40 72 30 86 18 90 7M63 52 75 58 88 74 88 86"/>
    </g>
    <path d="M35 20h26v5h7v8h5v26h-5v8H28v-8h-5V33h5v-8h7Z" fill="#725171"/>
    <path d="M37 24h21v5h7v8h4v20H27V37h5v-8h5Z" fill="#91698c"/>
    <path d="M32 53h32v5h5v20h-5v5H32v-5h-5V58h5Z" fill="#654565"/>
    <path d="M34 57h28v5h3v13h-3v4H34v-4h-3V62h3Z" fill="#805a7b"/>
    <path d="M34 59h10v12H34ZM52 59h10v12H52Z" fill="#fff3c7"/>
    <path d="M38 62h4v6h-4ZM54 62h4v6h-4Z" fill="#4d3452"/>
    <path d="M31 73h6v3h-6ZM59 73h6v3h-6Z" fill="#e8a5ae"/>
    <path d="M43 73h10v3H43Z" fill="#f3d1bc"/>
    <path d="M39 33h6v6h-6ZM51 33h6v6h-6ZM45 39h6v6h-6Z" fill="#edb28d"/>
  </svg>`;
  spider.innerHTML = art;
  document.querySelector('#spider-hug-body').innerHTML = art;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let x = 24, y = 110, target = null, frame = null, previous = 0;
  let hovering = false, keyboardFocus = false, hugging = false, hugWithKeyboard = false, releaseTimer = null, hoverTimer = null;
  let obstacles = [], nextObstacleCheck = 0;
  const enabled = () => document.documentElement.dataset.theme === 'light' && !document.hidden;
  const paused = () => reduced.matches || document.body.classList.contains('motion-paused');
  const bounds = () => ({ x: Math.max(8, innerWidth - spider.offsetWidth - 12), y: Math.max(8, innerHeight - spider.offsetHeight - 12) });
  function refreshObstacles() {
    obstacles = [...document.querySelectorAll('button:not(#halloween-spider), input, select, textarea, a[href]')]
      .map(element => element.getBoundingClientRect()).filter(rect => rect.width > 0 && rect.height > 0);
  }
  function blocked(px, py) {
    const size = spider.offsetWidth || 68;
    return obstacles.some(rect => px < rect.right + 8 && px + size > rect.left - 8 && py < rect.bottom + 8 && py + size > rect.top - 8);
  }
  function moveClear() {
    if (!blocked(x, y)) return;
    const limit = bounds(); let best = null, distance = Infinity;
    for (let cy = 8; cy <= limit.y; cy += 76) for (let cx = 8; cx <= limit.x; cx += 76) {
      const candidateDistance = (cx - x) ** 2 + (cy - y) ** 2;
      if (!blocked(cx, cy) && candidateDistance < distance) { best = { x: cx, y: cy }; distance = candidateDistance; }
    }
    if (best) { x = best.x; y = best.y; target = null; }
  }
  function destination(limit) {
    for (let attempt = 0; attempt < 32; attempt++) {
      const candidate = { x: 8 + Math.random() * (limit.x - 8), y: 8 + Math.random() * (limit.y - 8) };
      if (!blocked(candidate.x, candidate.y)) return candidate;
    }
    return { x, y };
  }
  function draw() { spider.style.transform = `translate(${x}px,${y}px)`; }
  function stop() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null; previous = 0; spider.classList.remove('is-crawling');
  }
  function tick(time) {
    frame = null;
    if (!enabled() || paused() || hugging || hovering || keyboardFocus) { stop(); return; }
    const dt = previous ? Math.min((time - previous) / 1000, .04) : 0;
    previous = time;
    if (time >= nextObstacleCheck) { refreshObstacles(); nextObstacleCheck = time + 250; moveClear(); }
    const limit = bounds();
    x = Math.max(8, Math.min(x, limit.x)); y = Math.max(8, Math.min(y, limit.y));
    if (!target) target = destination(limit);
    const dx = target.x - x, dy = target.y - y, distance = Math.hypot(dx, dy);
    const step = Math.min(distance, dt * 65);
    if (distance < 3) target = null;
    else {
      const nx = x + dx / distance * step, ny = y + dy / distance * step;
      if (blocked(nx, ny)) target = null;
      else { x = nx; y = ny; }
    }
    draw(); spider.classList.add('is-crawling'); frame = requestAnimationFrame(tick);
  }
  function release() {
    clearTimeout(releaseTimer); releaseTimer = null;
    // Step clear of the pointer so the released spider can crawl again.
    if (!hugWithKeyboard) {
      const limit = bounds();
      x = Math.max(8, Math.min(limit.x, x + (x + 96 <= limit.x ? 96 : -96)));
      hovering = false; keyboardFocus = false; target = null; draw();
    }
    hug.hidden = true; hugging = false; spider.classList.remove('is-hugging');
    status.textContent = ''; sync();
  }
  function sync() {
    spider.hidden = !enabled();
    spider.classList.toggle('is-resting', paused());
    spider.title = paused() ? 'Nhện đang nghỉ · bật chuyển động ở thanh trên để nhện bò' : 'Chạm nhện để được ôm';
    if (!enabled()) {
      stop(); clearTimeout(releaseTimer); clearTimeout(hoverTimer); releaseTimer = null;
      hovering = false; keyboardFocus = false;
      hug.hidden = true; hugging = false; spider.classList.remove('is-hugging'); status.textContent = ''; return;
    }
    const limit = bounds(); x = Math.max(8, Math.min(x, limit.x)); y = Math.max(8, Math.min(y, limit.y));
    refreshObstacles(); moveClear(); draw();
    if (paused() || hugging || hovering || keyboardFocus) stop();
    else if (frame === null) frame = requestAnimationFrame(tick);
    if (hugging && paused()) hug.classList.add('is-still');
  }
  spider.addEventListener('pointerenter', event => {
    if (event.pointerType === 'touch') return;
    clearTimeout(hoverTimer); hovering = true; sync();
    hoverTimer = setTimeout(() => { hovering = false; sync(); }, 1200);
  });
  spider.addEventListener('pointerleave', () => { clearTimeout(hoverTimer); hovering = false; sync(); });
  spider.addEventListener('focus', () => { keyboardFocus = spider.matches(':focus-visible'); sync(); });
  spider.addEventListener('blur', () => { keyboardFocus = false; sync(); });
  spider.addEventListener('click', event => {
    if (!enabled() || hugging) return;
    hugWithKeyboard = event.detail === 0;
    hugging = true; stop();
    hug.style.setProperty('--hug-x', `${x + spider.offsetWidth / 2 - innerWidth / 2}px`);
    hug.style.setProperty('--hug-y', `${y + spider.offsetHeight / 2 - innerHeight / 2}px`);
    hug.classList.toggle('is-still', paused());
    spider.classList.add('is-hugging'); hug.hidden = false;
    status.textContent = 'Nhện gửi bạn một cái ôm Halloween!';
    releaseTimer = setTimeout(release, paused() ? 1800 : 3400);
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && hugging) release(); });
  document.addEventListener('visibilitychange', sync);
  window.addEventListener('resize', () => { target = null; sync(); });
  reduced.addEventListener('change', sync);
  const observer = new MutationObserver(sync);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  const view = document.querySelector('#view-content');
  if (view) observer.observe(view, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
  draw(); sync();
});
