from pathlib import Path
import re

routes = {
    'Dashboard': '?page=Dashboard&auth=__AUTH__',
    'Xe vào': '?page=Xe+v%C3%A0o&auth=__AUTH__',
    'Xe ra': '?page=Xe+ra&auth=__AUTH__',
    'Cần kiểm tra': '?page=C%E1%BA%A7n+ki%E1%BB%83m+tra&auth=__AUTH__',
    'Nhật ký': '?page=Nh%E1%BA%ADt+k%C3%BD&auth=__AUTH__',
    'Tài khoản': '?page=T%C3%A0i+kho%E1%BA%A3n&auth=__AUTH__',
}

def visible_text(html: str) -> str:
    return re.sub(r'<[^>]+>', '', html).replace('\n', ' ')

anchor_pat = re.compile(r'<a\b[\s\S]*?</a>')
div_pat = re.compile(r'<div class="([^"]*)"([^>]*)>\s*(<span class="material-symbols-outlined"[^>]*>[\s\S]*?</span>)\s*([^<>]*?)\s*</div>')

for p in Path('frontend').glob('*_exact_html.py'):
    s = p.read_text(encoding='utf-8')
    old = s

    def patch_anchor(m):
        tag = m.group(0)
        text = visible_text(tag)
        for label, href in routes.items():
            if label in text:
                if 'href=' in tag:
                    tag = re.sub(r'href="[^"]*"', f'href="{href}"', tag, count=1)
                else:
                    tag = tag.replace('<a ', f'<a href="{href}" ', 1)
                if 'target="_parent"' not in tag:
                    tag = tag.replace('<a ', '<a target="_parent" ', 1)
                return tag
        return tag

    def patch_div(m):
        cls, extra, icon, text = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        if text in routes and 'cursor-pointer' in cls:
            return f'<a class="{cls}" href="{routes[text]}" target="_parent">{icon}{text}</a>'
        return m.group(0)

    s = anchor_pat.sub(patch_anchor, s)
    s = div_pat.sub(patch_div, s)

    if s != old:
        p.write_text(s, encoding='utf-8')
        print('updated', p.name)
