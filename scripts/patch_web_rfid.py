# -*- coding: utf-8 -*-
"""
Patch frontend/web/app.js with RFID, NFC, and dynamic QR features.
"""

new_methods = """  async entry() {
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
"""

with open('frontend/web/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

p1 = content.find('  async entry() {')
p2 = content.find('  async review() {')

if p1 != -1 and p2 != -1:
    patched = content[:p1] + new_methods + '\n' + content[p2:]
    with open('frontend/web/app.js', 'w', encoding='utf-8') as f:
        f.write(patched)
    print("SUCCESS: frontend/web/app.js successfully patched!")
else:
    print(f"FAILED: markers not found (p1={p1}, p2={p2})")
