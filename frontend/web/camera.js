'use strict';

// Camera frames enter the same validated image workflow as file uploads.
function bindCameraCapture(prefix, onCapture, onActive = () => {}) {
  const get = suffix => document.querySelector(`#${prefix}-camera-${suffix}`);
  const open = get('open'), panel = get('panel'), video = get('video');
  const shutter = get('shutter'), devices = get('devices'), message = get('message');
  let stream = null, generation = 0, disposed = false, pending = false, capturing = false;
  function tell(text, error = false) {
    message.textContent = text; message.classList.toggle('camera-error', error);
  }
  function stopStream() {
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = null;
    if (video.srcObject) video.pause();
    video.srcObject = null; shutter.disabled = true;
  }
  function close() {
    generation++; pending = false; capturing = false; stopStream();
    panel.hidden = true; open.disabled = false; devices.disabled = false;
    onActive(false);
  }
  function ready() {
    if (!stream || pending || capturing || !video.videoWidth || !video.videoHeight) return;
    shutter.disabled = false;
    tell(`Camera sẵn sàng · ${video.videoWidth} × ${video.videoHeight}`);
  }
  async function start(deviceId = '') {
    if (disposed || pending) return;
    const request = ++generation;
    stopStream(); capturing = false; pending = true; panel.hidden = false;
    onActive(true);
    open.disabled = true; devices.disabled = true; tell('Đang mở camera…');
    let acquired = null;
    try {
      const media = globalThis.navigator?.mediaDevices;
      if (globalThis.isSecureContext === false) throw new Error('Mở trang bằng HTTPS hoặc localhost để dùng camera. Trên điện thoại, bạn có thể chọn Camera điện thoại bên dưới.');
      if (!media?.getUserMedia) throw new Error('Trình duyệt này chưa hỗ trợ camera trực tiếp. Hãy mở bằng Chrome/Edge, hoặc dùng Camera điện thoại.');
      acquired = await media.getUserMedia({ audio: false, video: {
        width: { ideal: 1920 }, height: { ideal: 1080 },
        ...(deviceId ? { deviceId: { exact: deviceId } } : { facingMode: { ideal: 'environment' } }),
      } });
      if (disposed || request !== generation) { acquired.getTracks().forEach(track => track.stop()); return; }
      stream = acquired; video.srcObject = stream;
      stream.getVideoTracks().forEach(track => track.addEventListener('ended', () => {
        if (stream !== acquired) return;
        close(); panel.hidden = false; onActive(true); tell('Camera đã ngắt kết nối. Kiểm tra thiết bị rồi mở lại.', true);
      }));
      await video.play();
      if (disposed || request !== generation) { acquired.getTracks().forEach(track => track.stop()); return; }
      pending = false; open.disabled = false; devices.disabled = false;
      tell('Đang chờ hình từ camera…'); ready();
      // Device labels become available after camera permission is granted.
      try {
        const list = (await media.enumerateDevices()).filter(device => device.kind === 'videoinput');
        if (disposed || request !== generation) return;
        const active = acquired.getVideoTracks()[0]?.getSettings().deviceId;
        devices.innerHTML = '<option value="">Camera mặc định</option>' + list.map((device, index) =>
          `<option value="${esc(device.deviceId)}">${esc(device.label || `Camera ${index + 1}`)}</option>`).join('');
        devices.value = list.some(device => device.deviceId === active) ? active : '';
      } catch (_) { /* Preview remains usable when device listing is restricted. */ }
    } catch (error) {
      if (disposed || request !== generation) { acquired?.getTracks().forEach(track => track.stop()); return; }
      stopStream(); pending = false; open.disabled = false; devices.disabled = false;
      const explanations = {
        NotAllowedError: 'Chưa được cấp quyền camera. Cho phép camera trong trình duyệt rồi thử lại.',
        SecurityError: 'Trình duyệt đang chặn camera. Hãy mở trang bằng HTTPS hoặc localhost.',
        NotFoundError: 'Không tìm thấy camera. Kết nối webcam/USB, hoặc dùng camera điện thoại.',
        NotReadableError: 'Camera đang được ứng dụng khác sử dụng. Đóng ứng dụng đó rồi thử lại.',
        OverconstrainedError: 'Camera đã chọn không còn khả dụng. Chọn camera khác rồi thử lại.',
      };
      tell(explanations[error.name] || (error.name === 'Error' ? error.message : 'Không mở được camera. Kiểm tra thiết bị và quyền truy cập rồi thử lại.'), true);
    }
  }
  async function capture() {
    if (disposed || capturing || pending || !stream) return;
    if (!video.videoWidth || !video.videoHeight || video.readyState < 2) { tell('Chờ camera hiện hình rồi chụp lại.', true); return; }
    const request = generation;
    capturing = true; shutter.disabled = true;
    try {
      const canvas = document.createElement('canvas');
      const scale = Math.min(1, 2560 / Math.max(video.videoWidth, video.videoHeight));
      canvas.width = Math.round(video.videoWidth * scale); canvas.height = Math.round(video.videoHeight * scale);
      const context = canvas.getContext('2d');
      if (!context) throw new Error('Không tạo được ảnh từ camera. Hãy thử chụp lại.');
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', .92));
      if (disposed || request !== generation) return;
      if (!blob) throw new Error('Camera chưa tạo được ảnh. Hãy thử chụp lại.');
      const file = new File([blob], `camera-${prefix}-${Date.now()}.jpg`, { type: 'image/jpeg' });
      if (onCapture(file) !== false) close();
    } catch (error) { if (!disposed && request === generation) tell(error.message, true); }
    finally { if (!disposed && request === generation) { capturing = false; shutter.disabled = !stream || !video.videoWidth || !video.videoHeight; } }
  }
  open.addEventListener('click', () => start());
  get('close').addEventListener('click', close);
  shutter.addEventListener('click', capture);
  devices.addEventListener('change', () => start(devices.value));
  video.addEventListener('loadeddata', ready);
  const native = get('native');
  get('phone').addEventListener('click', () => { close(); native.click(); });
  native.addEventListener('change', () => { if (native.files[0]) onCapture(native.files[0]); native.value = ''; });
  const visibility = () => { if (document.hidden) close(); };
  const leave = () => close();
  const escape = event => { if (event.key === 'Escape' && !panel.hidden) close(); };
  document.addEventListener('visibilitychange', visibility);
  document.addEventListener('keydown', escape);
  globalThis.addEventListener?.('pagehide', leave);
  return { close, dispose() {
    disposed = true; close();
    document.removeEventListener('visibilitychange', visibility);
    document.removeEventListener('keydown', escape);
    globalThis.removeEventListener?.('pagehide', leave);
  } };
}
