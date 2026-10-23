# -*- coding: utf-8 -*-
"""Patch frontend/web/app.js to add RFID Card Management and Hardware Wedge support."""

from pathlib import Path

APP_JS = Path("frontend/web/app.js")
text = APP_JS.read_text(encoding="utf-8")
is_crlf = "\r\n" in text
nl = "\r\n" if is_crlf else "\n"

# 1. Update entry presets & enter keypress listener
old_entry_block = """    $('#btn-preset-staff').addEventListener('click', () => {
      $('#entry-card').value = 'UTH_STAFF_GV_01';
      $('#entry-plate').value = '51F-888.88';
      $('#entry-user-type').value = 'STAFF';
      toast('Đã nạp Thẻ Giảng viên mẫu (Miễn phí 0đ)');
    });"""

new_entry_block = """    $('#btn-preset-staff').addEventListener('click', () => {
      $('#entry-card').value = 'UTH_STAFF_GV_01';
      $('#entry-plate').value = '51F-888.88';
      $('#entry-user-type').value = 'STAFF';
      toast('Đã nạp Thẻ Giảng viên mẫu (Miễn phí 0đ)');
    });

    $('#entry-card').addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const val = $('#entry-card').value.trim();
        if (!val) return;
        try {
          const cRes = await api(`/cards/${encodeURIComponent(val)}`);
          if (cRes && cRes.ok && cRes.card) {
            const c = cRes.card;
            if (c.user_type) $('#entry-user-type').value = c.user_type;
            if (c.default_plate && !$('#entry-plate').value) $('#entry-plate').value = c.default_plate;
            toast(`Đã nhận diện: ${c.label} (${c.user_type})`, 'info');
          }
        } catch (_) {}
        $('#entry-submit').click();
      }
    });"""

if is_crlf:
    old_entry_block = old_entry_block.replace("\n", "\r\n")
    new_entry_block = new_entry_block.replace("\n", "\r\n")

if old_entry_block in text:
    text = text.replace(old_entry_block, new_entry_block)
    print("Added entry-card Enter listener.")

# 2. Update exit enter keypress listener
old_exit_block = """    $('#exit-card').addEventListener('input', (e) => matchCardToTicket(e.target.value));"""

new_exit_block = """    $('#exit-card').addEventListener('input', (e) => matchCardToTicket(e.target.value));
    $('#exit-card').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const val = $('#exit-card').value.trim();
        if (!val) return;
        matchCardToTicket(val);
        setTimeout(() => {
          if ($('#exit-ticket').value) {
            $('#exit-submit').click();
          }
        }, 100);
      }
    });"""

if is_crlf:
    old_exit_block = old_exit_block.replace("\n", "\r\n")
    new_exit_block = new_exit_block.replace("\n", "\r\n")

if old_exit_block in text:
    text = text.replace(old_exit_block, new_exit_block)
    print("Added exit-card Enter listener.")

# 3. Add RENDER.cards before RENDER ends
old_render_end = """        if (state.view === 'admin') await showView('admin');
      });
    }));
  },
};"""

cards_renderer = """        if (state.view === 'admin') await showView('admin');
      });
    }));
  },

  async cards() {
    const data = await api('/cards');
    if (state.view !== 'cards') return;
    const items = data.items || [];

    const slotCards = [1, 2, 3, 4, 5].map(i => {
      const found = items.find(c => c.card_uid === `CARD_WHITE_0${i}`) || items.find(c => (c.label || '').includes(`#${i}`));
      const assigned = found ? (found.card_uid.startsWith('CARD_WHITE_') ? 'Chưa gán UID' : found.card_uid) : 'Trống';
      const type = found?.user_type || 'STUDENT';
      const typeBadge = type === 'STAFF' ? '<span class=\"status-badge\" style=\"background:#10b981;color:#fff\">Giảng viên (0đ)</span>' : (type === 'GUEST' ? '<span class=\"status-badge\" style=\"background:#f59e0b;color:#fff\">Khách vãng lai</span>' : '<span class=\"status-badge\" style=\"background:#3b82f6;color:#fff\">Sinh viên (5k)</span>');
      return `
        <div style=\"background:var(--card-bg, rgba(255,255,255,0.04));padding:14px;border-radius:10px;border:1px solid rgba(255,255,255,0.08);display:flex;flex-direction:column;gap:8px\">
          <div style=\"display:flex;justify-content:space-between;align-items:center\">
            <strong>Thẻ Trắng #${i}</strong>
            ${typeBadge}
          </div>
          <div style=\"font-size:13px;color:var(--muted)\">Mã UID: <code style=\"color:#38bdf8;font-weight:bold\">${esc(assigned)}</code></div>
          <div style=\"font-size:12px;color:var(--muted)\">Biển số gán: <strong>${esc(found?.default_plate || '—')}</strong></div>
          <button type=\"button\" class=\"btn btn-sm btn-soft btn-assign-slot\" data-slot=\"${i}\" style=\"margin-top:6px\">
            Gán mã thẻ vừa quẹt vào Slot #${i}
          </button>
        </div>
      `;
    }).join('');

    $('#view-content').innerHTML = `
      <div style=\"display:flex;flex-direction:column;gap:20px\">
        <section class=\"card\" style=\"border:2px dashed #38bdf8;background:rgba(56,189,248,0.04)\">
          <div class=\"card-heading\">
            <h3>⚡ Kiểm tra Đầu đọc USB 13.56MHz & Quẹt Thẻ Tức thì</h3>
            <span class=\"status-badge\" style=\"background:#0ea5e9;color:#fff\">Live Wedge Reader</span>
          </div>
          <p style=\"margin:6px 0 14px;font-size:14px;color:var(--muted);line-height:1.5\">
            Cắm đầu đọc USB vào máy tính. Nhấp vào ô dưới và <strong>quẹt thẻ trắng hoặc thẻ sinh viên UTH</strong>. Đầu đọc sẽ kêu "Tít" và tự động hiển thị mã UID lên màn hình!
          </p>
          <div style=\"display:flex;gap:12px;align-items:center;flex-wrap:wrap\">
            <input id=\"card-wedge-test\" placeholder=\"Quẹt thẻ vào đây để đọc mã UID ngay lập tức...\" style=\"flex:1;min-width:280px;font-size:16px;font-family:monospace;padding:12px 16px;border:2px solid #38bdf8;border-radius:8px;background:rgba(0,0,0,0.2)\" autofocus />
            <span id=\"wedge-last-scanned\" style=\"padding:10px 16px;border-radius:8px;background:rgba(255,255,255,0.06);font-family:monospace;font-size:15px;font-weight:bold;color:#38bdf8\">
              Chưa có thẻ quẹt
            </span>
          </div>
          <div id=\"wedge-quick-actions\" style=\"margin-top:14px;display:none;padding:12px;background:rgba(16,185,129,0.1);border-radius:8px;border:1px solid #10b981\">
            <span style=\"font-size:13px;color:#10b981;font-weight:600\">Thao tác nhanh cho thẻ vừa đọc:</span>
            <div style=\"display:flex;gap:8px;flex-wrap:wrap;margin-top:8px\" id=\"quick-assign-buttons\"></div>
          </div>
        </section>

        <section class=\"card\">
          <div class=\"card-heading\">
            <h3>5 Thẻ Trắng Quản Lý (Combo 13.56MHz Shopee)</h3>
            <button type=\"button\" class=\"btn btn-sm btn-primary\" id=\"btn-refresh-cards\">Làm mới danh sách</button>
          </div>
          <p style=\"margin:4px 0 14px;font-size:13px;color:var(--muted)\">
            Khi nhận hàng, anh quẹt lần lượt từng thẻ vào ô trên, sau đó bấm nút Gán tương ứng để lưu vào hệ thống.
          </p>
          <div style=\"display:grid;grid-template-columns:repeat(auto-fit, minmax(230px, 1fr));gap:12px\">
            ${slotCards}
          </div>
        </section>

        <section class=\"card\">
          <div class=\"card-heading\">
            <h3>Tất cả thẻ RFID đã đăng ký (${items.length} thẻ)</h3>
          </div>
          <div class=\"table-wrap\">
            <table>
              <thead>
                <tr>
                  <th>Mã UID</th>
                  <th>Tên mô tả</th>
                  <th>Phân loại</th>
                  <th>Biển số gán</th>
                  <th>Ghi chú</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                ${items.map(c => `
                  <tr>
                    <td><code style=\"color:#38bdf8;font-weight:bold\">${esc(c.card_uid)}</code></td>
                    <td><strong>${esc(c.label)}</strong></td>
                    <td>${c.user_type === 'STAFF' ? '<span class=\"status-badge\" style=\"background:#10b981;color:#fff\">Giảng viên (0đ)</span>' : (c.user_type === 'GUEST' ? '<span class=\"status-badge\" style=\"background:#f59e0b;color:#fff\">Khách vãng lai</span>' : '<span class=\"status-badge\" style=\"background:#3b82f6;color:#fff\">Sinh viên (5k)</span>')}</td>
                    <td><strong>${esc(c.default_plate || '—')}</strong></td>
                    <td style=\"color:var(--muted);font-size:13px\">${esc(c.note || '—')}</td>
                    <td>
                      <button type=\"button\" class=\"text-btn btn-delete-card\" data-uid=\"${esc(c.card_uid)}\" style=\"color:#ef4444\">Xóa</button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    `;

    let lastScannedUid = '';
    const testInput = $('#card-wedge-test');
    const updateScannedUid = (uid) => {
      lastScannedUid = (uid || '').trim().toUpperCase();
      if (!lastScannedUid) return;
      $('#wedge-last-scanned').textContent = `Mã vừa đọc: ${lastScannedUid}`;
      $('#wedge-quick-actions').style.display = 'block';
      const container = $('#quick-assign-buttons');
      container.innerHTML = [1, 2, 3, 4, 5].map(i => `
        <button type=\"button\" class=\"btn btn-sm btn-soft btn-quick-assign\" data-slot=\"${i}\">
          Gán Thẻ Trắng #${i}
        </button>
      `).join('') + `
        <button type=\"button\" class=\"btn btn-sm btn-primary\" id=\"btn-assign-uth-sv\">
          Gán Thẻ SV UTH (${lastScannedUid})
        </button>
      `;

      container.querySelectorAll('.btn-quick-assign').forEach(b => {
        b.addEventListener('click', async () => {
          const slot = b.dataset.slot;
          await api('/cards/assign-slot', {
            method: 'POST',
            body: new URLSearchParams({ slot_number: slot, real_card_uid: lastScannedUid })
          });
          toast(`Đã gán Thẻ Trắng #${slot} thành công!`, 'success');
          showView('cards');
        });
      });

      const btnUth = $('#btn-assign-uth-sv');
      if (btnUth) {
        btnUth.addEventListener('click', async () => {
          await api('/cards', {
            method: 'POST',
            body: new URLSearchParams({
              card_uid: lastScannedUid,
              label: 'Thẻ Sinh viên UTH - Nguyễn Quang Huy',
              user_type: 'STUDENT',
              default_plate: '59X3-123.45',
              note: 'Thẻ sinh viên Napas Contactless 13.56MHz'
            })
          });
          toast(`Đã gán thẻ SV UTH thành công!`, 'success');
          showView('cards');
        });
      }
    };

    testInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        updateScannedUid(testInput.value);
        testInput.value = '';
      }
    });

    testInput.addEventListener('input', (e) => {
      if (e.target.value.length >= 8) {
        updateScannedUid(e.target.value);
      }
    });

    document.querySelectorAll('.btn-assign-slot').forEach(btn => {
      btn.addEventListener('click', async () => {
        const slot = btn.dataset.slot;
        const targetUid = lastScannedUid || prompt(`Nhập mã UID thực tế cho Thẻ Trắng #${slot}:`);
        if (!targetUid) return;
        await api('/cards/assign-slot', {
          method: 'POST',
          body: new URLSearchParams({ slot_number: slot, real_card_uid: targetUid })
        });
        toast(`Đã gán Thẻ Trắng #${slot} vào UID ${targetUid}`, 'success');
        showView('cards');
      });
    });

    document.querySelectorAll('.btn-delete-card').forEach(btn => {
      btn.addEventListener('click', async () => {
        const uid = btn.dataset.uid;
        if (!confirm(`Xóa thẻ ${uid}?`)) return;
        await api(`/cards/${encodeURIComponent(uid)}`, { method: 'DELETE' });
        toast(`Đã xóa thẻ ${uid}`);
        showView('cards');
      });
    });

    $('#btn-refresh-cards').addEventListener('click', () => showView('cards'));
  },
};"""

if is_crlf:
    old_render_end = old_render_end.replace("\n", "\r\n")
    cards_renderer = cards_renderer.replace("\n", "\r\n")

if old_render_end in text:
    text = text.replace(old_render_end, cards_renderer)
    print("Added cards renderer.")

APP_JS.write_text(text, encoding="utf-8")
print("app.js successfully updated.")
