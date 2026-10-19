from __future__ import annotations


def get_exact_entry_html(username: str = "Admin User") -> str:
    return r'''<!DOCTYPE html>
<html class="light" lang="vi"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            "colors": {
                    "on-background": "#191c1e",
                    "primary": "#000000",
                    "secondary-fixed-dim": "#4cd7f6",
                    "on-secondary-container": "#006172",
                    "on-surface": "#191c1e",
                    "surface-dim": "#d8dadc",
                    "outline-variant": "#c6c6cd",
                    "error": "#ba1a1a",
                    "surface-container-high": "#e6e8ea",
                    "on-tertiary": "#ffffff",
                    "tertiary-container": "#001a42",
                    "on-primary-fixed-variant": "#3f465c",
                    "tertiary-fixed": "#d8e2ff",
                    "on-secondary-fixed": "#001f26",
                    "secondary-container": "#57dffe",
                    "on-tertiary-fixed-variant": "#004395",
                    "secondary-fixed": "#acedff",
                    "inverse-surface": "#2d3133",
                    "on-error": "#ffffff",
                    "on-surface-variant": "#45464d",
                    "on-tertiary-container": "#3980f4",
                    "on-primary-fixed": "#131b2e",
                    "on-primary": "#ffffff",
                    "outline": "#76777d",
                    "surface-container-low": "#f2f4f6",
                    "tertiary-fixed-dim": "#adc6ff",
                    "surface-variant": "#e0e3e5",
                    "secondary": "#00687a",
                    "surface-bright": "#f7f9fb",
                    "inverse-primary": "#bec6e0",
                    "tertiary": "#000000",
                    "on-primary-container": "#7c839b",
                    "surface-container-lowest": "#ffffff",
                    "error-container": "#ffdad6",
                    "on-error-container": "#93000a",
                    "primary-fixed-dim": "#bec6e0",
                    "surface-container-highest": "#e0e3e5",
                    "on-secondary-fixed-variant": "#004e5c",
                    "inverse-on-surface": "#eff1f3",
                    "surface-tint": "#565e74",
                    "primary-fixed": "#dae2fd",
                    "background": "#f7f9fb",
                    "on-secondary": "#ffffff",
                    "surface-container": "#eceef0",
                    "surface": "#f7f9fb",
                    "on-tertiary-fixed": "#001a42",
                    "primary-container": "#131b2e"
            },
            "borderRadius": {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
            "spacing": {"unit": "4px", "gutter": "20px", "xs": "4px", "lg": "24px", "container-padding": "24px", "sm": "8px", "md": "16px", "xl": "32px"},
            "fontFamily": {"body-base": ["Inter"], "label-caps": ["Inter"], "body-sm": ["Inter"], "plate-display": ["Space Grotesk"], "h1": ["Inter"], "h2": ["Inter"]},
            "fontSize": {
                    "body-base": ["16px", {"lineHeight": "1.5", "letterSpacing": "0", "fontWeight": "400"}],
                    "label-caps": ["12px", {"lineHeight": "1", "letterSpacing": "0.05em", "fontWeight": "600"}],
                    "body-sm": ["14px", {"lineHeight": "1.5", "letterSpacing": "0", "fontWeight": "400"}],
                    "plate-display": ["20px", {"lineHeight": "1", "letterSpacing": "0.05em", "fontWeight": "700"}],
                    "h1": ["32px", {"lineHeight": "1.2", "letterSpacing": "-0.02em", "fontWeight": "700"}],
                    "h2": ["24px", {"lineHeight": "1.3", "letterSpacing": "-0.01em", "fontWeight": "600"}]
            }
          },
        },
      }
</script>
<style>
        html, body { margin: 0; width: 100%; min-height: 100%; overflow-x: hidden; }
        .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
        .glass-card { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(226, 232, 240, 0.8); }
</style>
</head>
<body class="bg-background font-body-base text-on-background min-h-screen">
<aside class="h-screen w-64 fixed left-0 top-0 z-50 bg-[#0F172A] border-r border-slate-800 shadow-2xl shadow-black flex flex-col h-full py-6 font-body-sm">
<div class="px-6 mb-8"><h1 class="text-xl font-bold tracking-tight text-white">ITS Parking</h1><p class="text-cyan-400 text-[10px] font-medium tracking-widest uppercase mt-1">AI Pipeline: YOLOv9 (95.9%)</p></div>
<nav class="flex-1 space-y-1">
<a target="_top" onclick="window.top.location.href='?page=Dashboard&auth=__AUTH__'; return false;" class="text-slate-400 px-6 py-3 flex items-center gap-3 hover:text-white transition-all duration-300 group" href="?page=Dashboard&auth=__AUTH__"><span class="material-symbols-outlined" data-icon="dashboard">dashboard</span>Dashboard</a>
<a target="_top" onclick="window.top.location.href='?page=Xe+v%C3%A0o&auth=__AUTH__'; return false;" class="bg-cyan-500/10 text-cyan-400 border-r-4 border-cyan-400 px-6 py-3 flex items-center gap-3 transition-all duration-300" href="?page=Xe+v%C3%A0o&auth=__AUTH__"><span class="material-symbols-outlined" data-icon="login">login</span>Xe vào</a>
<a target="_top" onclick="window.top.location.href='?page=Xe+ra&auth=__AUTH__'; return false;" class="text-slate-400 px-6 py-3 flex items-center gap-3 hover:text-white transition-all duration-300 group" href="?page=Xe+ra&auth=__AUTH__"><span class="material-symbols-outlined" data-icon="logout">logout</span>Xe ra</a>
<a target="_top" onclick="window.top.location.href='?page=C%E1%BA%A7n+ki%E1%BB%83m+tra&auth=__AUTH__'; return false;" class="text-slate-400 px-6 py-3 flex items-center gap-3 hover:text-white transition-all duration-300 group" href="?page=C%E1%BA%A7n+ki%E1%BB%83m+tra&auth=__AUTH__"><span class="material-symbols-outlined" data-icon="fact_check">fact_check</span>Cần kiểm tra</a>
<a target="_top" onclick="window.top.location.href='?page=Nh%E1%BA%ADt+k%C3%BD&auth=__AUTH__'; return false;" class="text-slate-400 px-6 py-3 flex items-center gap-3 hover:text-white transition-all duration-300 group" href="?page=Nh%E1%BA%ADt+k%C3%BD&auth=__AUTH__"><span class="material-symbols-outlined" data-icon="history">history</span>Nhật ký</a>
<a target="_top" onclick="window.top.location.href='?page=T%C3%A0i+kho%E1%BA%A3n&auth=__AUTH__'; return false;" class="text-slate-400 px-6 py-3 flex items-center gap-3 hover:text-white transition-all duration-300 group" href="?page=T%C3%A0i+kho%E1%BA%A3n&auth=__AUTH__"><span class="material-symbols-outlined" data-icon="manage_accounts">manage_accounts</span>Tài khoản</a>
</nav>
<div class="px-6 mt-auto pt-6 border-t border-slate-800">
<a class="text-slate-400 py-2 flex items-center gap-3 hover:text-white text-xs mb-2" href="#"><span class="material-symbols-outlined text-sm" data-icon="analytics">analytics</span>System Status</a>
<a class="text-slate-400 py-2 flex items-center gap-3 hover:text-white text-xs mb-6" href="#"><span class="material-symbols-outlined text-sm" data-icon="menu_book">menu_book</span>Documentation</a>
<button class="w-full bg-slate-800 hover:bg-slate-700 text-white py-2 rounded-lg text-sm font-semibold transition-colors">Logout</button>
</div>
</aside>
<main class="ml-64 min-h-screen flex flex-col">
<header class="bg-white/70 backdrop-blur-md sticky top-0 z-40 border-b border-slate-200 shadow-sm shadow-slate-200/50 flex items-center justify-between px-6 h-16 w-full ml-auto">
<div class="flex items-center gap-4"><h2 class="font-h2 text-h2 text-primary">Xử lý xe vào</h2><span class="px-3 py-1 bg-cyan-100 text-cyan-700 text-[10px] font-bold rounded-full uppercase tracking-tighter">Live Monitor</span></div>
<div class="flex items-center gap-6"><div class="flex items-center gap-4"><span class="material-symbols-outlined text-slate-500 cursor-pointer hover:text-cyan-600 transition-colors" data-icon="notifications">notifications</span><span class="material-symbols-outlined text-slate-500 cursor-pointer hover:text-cyan-600 transition-colors" data-icon="sensors">sensors</span><span class="material-symbols-outlined text-slate-500 cursor-pointer hover:text-cyan-600 transition-colors" data-icon="database">database</span></div><div class="h-8 w-[1px] bg-slate-200"></div><div class="flex items-center gap-3"><div class="text-right"><p class="text-xs font-bold text-slate-900">Admin User</p><p class="text-[10px] text-slate-500">Gate A1-West</p></div><img alt="User Avatar" class="w-10 h-10 rounded-full border-2 border-white shadow-sm object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA5MO3hvgS2Iyg2wu-Lb5yyjzqod7UOgrP5RPG4rLjAD04Mi7Fzsnrw_qgUl1bKM42X1cBhEYybIleQf8Pxs3ycWkXmC_Q1rIF5aba5pxJ3qNZ1-AxzhW0Y7WV3StvPNcOl4FMGHiPJbtV7rD1xf1_evTx2SblMk2NtWjXx9jm-QOOfOhK8ePOpGPI1-GaWfL9Uub0FIB4hZB6TDHnAWyeRMhyRiZ1FEqZ6AZi1mtEJnjxTtE9OHcZlhIjbBhLSUGS8iBhhEg176HuU"/></div></div>
</header>
<div class="p-lg flex-1">
<div class="mb-xl max-w-4xl mx-auto"><div class="flex items-center justify-between relative"><div class="absolute top-1/2 left-0 w-full h-[2px] bg-slate-200 -z-10 -translate-y-1/2"></div><div class="flex flex-col items-center gap-2"><div class="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold shadow-lg ring-4 ring-white">1</div><span class="text-[11px] font-bold text-slate-900 uppercase">Chọn ảnh</span></div><div class="flex flex-col items-center gap-2"><div class="w-10 h-10 rounded-full bg-cyan-500 text-white flex items-center justify-center font-bold shadow-lg ring-4 ring-white ring-offset-2 ring-offset-cyan-500/20">2</div><span class="text-[11px] font-bold text-cyan-600 uppercase">Nhận diện</span></div><div class="flex flex-col items-center gap-2"><div class="w-10 h-10 rounded-full bg-white border-2 border-slate-200 text-slate-400 flex items-center justify-center font-bold">3</div><span class="text-[11px] font-bold text-slate-400 uppercase">Xác nhận</span></div><div class="flex flex-col items-center gap-2"><div class="w-10 h-10 rounded-full bg-white border-2 border-slate-200 text-slate-400 flex items-center justify-center font-bold">4</div><span class="text-[11px] font-bold text-slate-400 uppercase">Tạo ticket</span></div></div></div>
<div class="grid grid-cols-12 gap-gutter">
<div class="col-span-12 lg:col-span-7 space-y-gutter"><div class="bg-white border-2 border-dashed border-slate-300 rounded-xl p-xl flex flex-col items-center justify-center text-center hover:border-cyan-400 transition-all group cursor-pointer"><div class="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center mb-md group-hover:bg-cyan-50 transition-colors"><span class="material-symbols-outlined text-slate-400 text-3xl group-hover:text-cyan-500" data-icon="photo_camera">photo_camera</span></div><h3 class="font-h2 text-body-base font-semibold text-on-surface mb-xs">Tải ảnh biển số xe vào</h3><p class="text-body-sm text-slate-500">Hỗ trợ JPG, PNG • Kéo thả hoặc click để chọn</p></div>
<div class="grid grid-cols-2 gap-4"><div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm"><p class="text-[10px] font-bold text-slate-500 uppercase mb-3 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]" data-icon="image">image</span>Original image</p><div class="aspect-video rounded-lg overflow-hidden bg-slate-100 border border-slate-100"><img alt="Original Vehicle Capture" class="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAO7cUwCnPnkg6qsoetiirNw0TYPPNV5ti7uNvYGRqst4EnwhWIBeIeXXlEKOrQKV7TGN5mGbHYFZCAtje_WapRkeQ1tyeq_fFcpVD_iBTL19eB589BQ8lIXRPpFPwTrGvAB0tHowGOe2KsJGboDtnYqneDeZ7-89Dn0rOU7cHLYY7VZK65ONKasYKL3xA1MHdrwc8em_k-RY7JG6wdroU9IbC5Tly-G0zwphJhn9GYle-XR3nLE29GPCCAJ2fl4U2LZ3RpIR0AKjg6"/></div></div><div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm relative overflow-hidden"><div class="absolute top-0 right-0 p-2"><span class="bg-cyan-500 text-white text-[8px] font-black px-2 py-1 rounded">DETECTED</span></div><p class="text-[10px] font-bold text-slate-500 uppercase mb-3 flex items-center gap-1"><span class="material-symbols-outlined text-[14px]" data-icon="crop">crop</span>Annotated crop</p><div class="aspect-video rounded-lg overflow-hidden bg-slate-900 border-2 border-cyan-400 flex items-center justify-center"><img alt="Annotated Plate Crop" class="w-full h-full object-contain scale-150" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBQA0jKxK4H3FkhUGMetCBdyuQZv-E--vq_EKh7ZaX5kgfL6TyWW3vXaT6hY3ALihanzd3W9Z4foF7JCQRmGrVjMZaOJaqYHeWxUJ77O1nC0qS6gC7kO4kS1EhpxeTo0zKYidFK-vQ5CRlJE_v0kvERqyc23WczrybFpKUdh2vedhEftmA-TAVGXR0DGHWYS4gu8wnjBi4fSoJNMORhm4JMwLqzk5ySduG0Fr_gbMNlRHdcN156hielRGTf5mkLxji-3S6VSzMG0Vqu"/></div></div></div></div>
<div class="col-span-12 lg:col-span-5 space-y-gutter"><div class="glass-card rounded-xl p-lg shadow-sm border-l-4 border-l-cyan-500"><div class="flex justify-between items-center mb-3"><h4 class="text-body-sm font-bold text-slate-900 uppercase tracking-tight">Đang xử lý</h4><span class="text-cyan-600 font-black text-body-base">76%</span></div><div class="w-full bg-slate-200 h-2 rounded-full mb-4 overflow-hidden"><div class="bg-cyan-500 h-full w-[76%] rounded-full shadow-[0_0_8px_rgba(6,182,212,0.5)]"></div></div><div class="flex items-center gap-2 text-slate-600"><span class="material-symbols-outlined text-[18px] animate-spin" data-icon="settings">settings</span><span class="text-body-sm">OCR đang đọc ký tự...</span></div></div>
<div class="bg-white rounded-xl p-lg border border-slate-200 shadow-sm"><div class="flex items-center justify-between mb-6"><span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">AI Result Analysis</span><span class="flex items-center gap-1 text-[11px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded"><span class="material-symbols-outlined text-[14px]" data-icon="verified" data-weight="fill">verified</span>Confidence 1.00</span></div><div class="flex flex-col items-center justify-center py-6 bg-slate-50 rounded-lg border border-slate-100 mb-6"><div class="bg-white border-[3px] border-black rounded-md px-6 py-2 shadow-sm flex items-center gap-4 relative"><div class="absolute left-0 top-0 bottom-0 w-3 bg-blue-700 rounded-l-[2px]"></div><span class="font-plate-display text-[32px] text-black tracking-widest ml-2 uppercase">65-LI 007.80</span></div></div><div class="grid grid-cols-2 gap-4"><div class="bg-slate-50 p-3 rounded-lg"><p class="text-[9px] font-bold text-slate-400 uppercase mb-1">Engine</p><p class="text-body-sm font-mono font-bold text-slate-700">fast-alpr-easyocr</p></div><div class="bg-slate-50 p-3 rounded-lg"><p class="text-[9px] font-bold text-slate-400 uppercase mb-1">Latency</p><p class="text-body-sm font-mono font-bold text-slate-700">4.56s</p></div></div></div>
<div class="bg-primary-container rounded-xl p-lg shadow-xl ring-1 ring-slate-800"><label class="block text-[10px] font-bold text-cyan-400 uppercase mb-3 tracking-widest">Biển số xác nhận</label><div class="relative mb-6"><input class="w-full bg-slate-900 border-slate-700 text-white font-plate-display text-2xl px-4 py-4 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 transition-all uppercase tracking-widest" placeholder="Nhập biển số xe..." type="text" value="65-LI 007.80"/><span class="absolute right-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-cyan-400" data-icon="edit">edit</span></div><button class="w-full bg-cyan-500 hover:bg-cyan-400 active:scale-95 text-primary font-bold py-4 rounded-xl shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-2"><span class="material-symbols-outlined font-bold" data-icon="check_circle">check_circle</span>Xác nhận xe vào</button></div></div>
</div></div>
<div class="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 opacity-0 pointer-events-none transition-all duration-500 transform translate-y-4"><div class="bg-slate-900 text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-4 border border-slate-700"><div class="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center"><span class="material-symbols-outlined text-cyan-400" data-icon="check_circle" data-weight="fill">check_circle</span></div><div><h5 class="font-bold text-body-base">Tạo ticket thành công!</h5><p class="text-[11px] text-slate-400 uppercase tracking-widest">Transaction ID: #ITS-29384-TX</p></div><button class="ml-4 p-2 hover:bg-slate-800 rounded-full transition-colors"><span class="material-symbols-outlined text-slate-500" data-icon="close">close</span></button></div></div>
</main>
<script>
(function () {
  function go(url) {
    try {
      const absoluteUrl = new URL(url, window.location.origin).toString();
      if (window.top && window.top !== window) {
        window.top.location.assign(absoluteUrl);
      } else if (window.parent && window.parent !== window) {
        window.parent.location.assign(absoluteUrl);
      } else {
        window.location.assign(absoluteUrl);
      }
    } catch (error) {
      window.location.href = url;
    }
  }

  document.addEventListener('click', function (event) {
    const link = event.target.closest('a[href*="page="]');
    if (!link) return;
    event.preventDefault();
    event.stopPropagation();
    go(link.getAttribute('href'));
  }, true);
})();
</script>
</body></html>'''
