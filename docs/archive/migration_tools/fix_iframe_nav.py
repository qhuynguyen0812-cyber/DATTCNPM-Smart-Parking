from pathlib import Path
import re

for p in Path('frontend').glob('*_exact_html.py'):
    s = p.read_text(encoding='utf-8')
    old = s

    def patch(m):
        tag = m.group(0)
        href_match = re.search(r'href="([^"]*page=[^"]*)"', tag)
        if not href_match:
            return tag
        url = href_match.group(1)
        tag = re.sub(r'\s+target="[^"]*"', '', tag)
        tag = re.sub(r'\s+onclick="[^"]*"', '', tag)
        tag = tag.replace('<a ', f'<a target="_top" onclick="window.top.location.href=\'{url}\'; return false;" ', 1)
        return tag

    s = re.sub(r'<a\b[^>]*href="[^"]*page=[^"]*"[^>]*>', patch, s)
    if s != old:
        p.write_text(s, encoding='utf-8')
        print('updated', p.name)
