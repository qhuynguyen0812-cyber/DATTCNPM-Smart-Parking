# -*- coding: utf-8 -*-
"""
Patch app.js with real-time wireless phone scanner listener.
"""

listener_code = """
/* ====== WIRELESS PHONE SCANNER POLLING ====== */
let lastScannerTs = Date.now() / 1000;
let scannerPollInterval = null;

function initWirelessScannerListener() {
  if (scannerPollInterval) clearInterval(scannerPollInterval);
  scannerPollInterval = setInterval(async () => {
    if (state.view !== 'entry' && state.view !== 'exit') return;
    try {
      const res = await fetch(`/scanner/poll?since=${lastScannerTs}`);
      const data = await res.json();
      if (data.ok && data.has_new && data.scan) {
        lastScannerTs = data.scan.timestamp;
        const scan = data.scan;
        toast(`📱 Đã nhận thẻ từ điện thoại: ${scan.card_id}`, 'success');

        if (state.view === 'entry') {
          const cardInput = $('#entry-card');
          if (cardInput) {
            cardInput.value = scan.card_id;
            cardInput.style.borderColor = '#10b981';
            setTimeout(() => cardInput.style.borderColor = '', 2000);
          }
          if (scan.plate_text && $('#entry-plate')) $('#entry-plate').value = scan.plate_text;
          if (scan.user_type && $('#entry-user-type')) $('#entry-user-type').value = scan.user_type;
        } else if (state.view === 'exit') {
          const exitCard = $('#exit-card');
          if (exitCard) {
            exitCard.value = scan.card_id;
            exitCard.dispatchEvent(new Event('input'));
          }
        }
      }
    } catch (e) {}
  }, 1000);
}

// Call on startup
initWirelessScannerListener();
"""

with open('frontend/web/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Add listener at the end of app.js if not present
if 'initWirelessScannerListener' not in content:
    content = content + "\n" + listener_code
    with open('frontend/web/app.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Wireless phone scanner listener appended to app.js")
else:
    print("Already present")
