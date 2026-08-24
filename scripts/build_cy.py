#!/usr/bin/env python3
"""Generate the Welsh site under /cy/ from the English pages.

The Welsh pages are built, never hand-edited: English is the single source of
truth for structure, and i18n/cy.json supplies the prose. Running this after any
English edit keeps the two languages from drifting apart.

It also patches the English pages in place, because the hreflang pairing and the
language switcher have to exist on both sides to be worth anything.
"""
import json, os, re, sys
import cy_lib as L

SITE = 'https://www.walesdampproofing.co.uk'
OUT = os.path.join(L.ROOT, 'cy')

# Slugs that are pages, so /cy/ prefixing does not catch /favicon.svg.
SLUGS = {p[:-5] for p in L.pages()}

MARK = '<!--i18n-->'   # so the injected block can be replaced, not duplicated


def path_for(name):
    return '/' if name == 'index.html' else '/' + name[:-5]


def alternates(name):
    en, cy = path_for(name), '/cy' + path_for(name)
    if cy.endswith('/cy/'):
        cy = '/cy/'
    return (f'{MARK}\n'
            f'<link rel="alternate" hreflang="en-GB" href="{SITE}{en}">\n'
            f'<link rel="alternate" hreflang="cy" href="{SITE}{cy}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}{en}">')


def inject_head(html, block):
    """Put the alternates just before </head>, replacing any earlier run's."""
    html = re.sub(re.escape(MARK) + r'\n(?:<link rel="alternate"[^>]*>\n?)*', '', html)
    return html.replace('</head>', block + '\n</head>', 1)


def switcher(html, href, label, lang):
    """Add or update the other language's link at the end of the main nav."""
    html = re.sub(r'\s*<a class="lang"[^>]*>.*?</a>', '', html, flags=re.S)
    link = (f'\n      <a class="lang" href="{href}" hreflang="{lang}" '
            f'lang="{lang}" rel="alternate">{label}</a>')
    return html.replace('    </nav>', link + '\n    </nav>', 1)


def relink(html):
    """Point page links, canonical and og:url at the Welsh copies."""
    def href(m):
        slug = m.group(2)
        if slug == '/' or slug.lstrip('/') in SLUGS:
            return f'{m.group(1)}="/cy{"" if slug == "/" else slug}{"/" if slug == "/" else ""}"'
        return m.group(0)
    html = re.sub(r'\b(href|action)="(/[^":]*)"', href, html)
    # Absolute self-references in canonical, og:url and JSON-LD.
    def absolute(m):
        tail = m.group(1)
        if tail in ('', '/') or tail.strip('/') in SLUGS:
            return SITE + '/cy' + (tail if tail not in ('', '/') else '/')
        return m.group(0)
    return re.sub(re.escape(SITE) + r'(/[\w-]*/?|)(?=["\s])', absolute, html)


def scripts(html, table, missing):
    """Swap the user-facing string literals inside <script>.

    Only literals listed in cy.script.json are touched — an allowlist, because
    guessing which literal in a script is prose would eventually rewrite a
    selector or a CSS declaration and break the page silently.
    """
    wanted = L.load('cy.script.json')
    if not wanted:
        return html
    out, last = [], 0
    for m in re.finditer(r'<script>(.*?)</script>', html, re.S):
        body = m.group(1)
        for en, cy in wanted.items():
            for q in ("'", '"'):
                # Welsh is full of apostrophes (mae'n, halwynau'r), so the
                # delimiter has to be escaped or the literal ends early and
                # takes the rest of the script with it.
                esc = cy.replace('\\', '\\\\').replace(q, '\\' + q)
                body = body.replace(q + en + q, q + esc + q)
        out.append(html[last:m.start(1)])
        out.append(body)
        last = m.end(1)
    out.append(html[last:])
    return ''.join(out)


def translate(html, table, missing):
    spans = [(a, b, None) for a, b in L.segments(html)]
    spans += [(a, b, v) for a, b, v in L.jsonld_spans(html)]
    for start, end, jsonval in sorted(spans, reverse=True):
        if jsonval is not None:
            cy = table.get(L.norm(jsonval))
            if cy is None:
                missing.add(L.norm(jsonval))
                continue
            # Re-encode so quotes and backslashes stay legal inside the JSON.
            html = html[:start] + json.dumps(cy, ensure_ascii=False)[1:-1] + html[end:]
            continue
        key, kept = L.mask(html[start:end])
        if not L.translatable(key):
            continue
        cy = table.get(key)
        if cy is None:
            missing.add(key)
            continue
        html = html[:start] + L.unmask(cy, kept) + html[end:]
    return html


def audit(name, html):
    """Welsh runs longer than English, so titles and descriptions drift over
    the length Google will show. Report anything that has."""
    import re as _re
    out = []
    m = _re.search(r'<title>(.*?)</title>', html, _re.S)
    if m and len(L.norm(m.group(1))) > 60:
        out.append(f'{name}: title {len(L.norm(m.group(1)))} chars')
    m = _re.search(r'<meta name="description" content="(.*?)"', html, _re.S)
    if m and len(L.norm(m.group(1))) > 158:
        out.append(f'{name}: description {len(L.norm(m.group(1)))} chars')
    return out


PRIORITY = {'index.html': '1.0', 'about.html': '0.6'}


def sitemap():
    """Rewrite sitemap.xml with both languages and their hreflang pairing.

    Generating it here rather than by hand is the only way eighteen pages in
    two languages stay in step with what actually exists on disk.
    """
    import datetime
    today = datetime.date.today().isoformat()
    rows = []
    for name in L.pages():
        en, cy = SITE + path_for(name), SITE + '/cy' + path_for(name)
        if name == 'index.html':
            cy = SITE + '/cy/'
        pri = PRIORITY.get(name, '0.8')
        for loc, other, lang, olang in ((en, cy, 'en-GB', 'cy'),
                                        (cy, en, 'cy', 'en-GB')):
            rows.append(
                f'  <url>\n'
                f'    <loc>{loc}</loc>\n'
                f'    <lastmod>{today}</lastmod>\n'
                f'    <changefreq>monthly</changefreq>\n'
                f'    <priority>{pri}</priority>\n'
                f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{loc}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="{olang}" href="{other}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en}"/>\n'
                f'  </url>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
           '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + '\n'.join(rows) + '\n</urlset>\n')
    open(os.path.join(L.ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(xml)
    return len(rows)


def check_scripts(name, html):
    """Parse the generated page's inline JS.

    Substituting Welsh into a string literal is the one edit in this build that
    can produce a syntactically broken page, so it is checked rather than
    assumed. Skipped silently where node is unavailable.
    """
    import shutil, subprocess, tempfile
    node = shutil.which('node')
    if not node:
        return []
    js = '\n'.join(re.findall(r'<script>(.*?)</script>', html, re.S))
    if not js.strip():
        return []
    with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8',
                                     delete=False) as fh:
        fh.write(js)
        path = fh.name
    try:
        r = subprocess.run([node, '--check', path], capture_output=True, text=True)
        if r.returncode:
            first = (r.stderr.strip().splitlines() or [''])[-1]
            return [f'{name}: inline JS does not parse — {first}']
        return []
    finally:
        os.unlink(path)


def build():
    table = L.load('cy.json')
    missing, long_meta, broken = set(), [], []
    os.makedirs(OUT, exist_ok=True)
    for name in L.pages():
        src = open(os.path.join(L.ROOT, name), encoding='utf-8').read()

        # English side: pair it with the Welsh page and offer the switch.
        en = src
        if 'og:locale' not in en:
            en = en.replace('<meta property="og:type"',
                            '<meta property="og:locale" content="en_GB">\n'
                            '<meta property="og:type"', 1)
        en = inject_head(en, alternates(name))
        cy_href = '/cy' + path_for(name)
        en = switcher(en, '/cy/' if cy_href == '/cy/' else cy_href, 'Cymraeg', 'cy')
        if en != src:
            open(os.path.join(L.ROOT, name), 'w', encoding='utf-8').write(en)

        # Welsh side, generated from the English source. The switcher is
        # stripped first: it is re-added below in the other language.
        bare = re.sub(r'\s*<a class="lang"[^>]*>.*?</a>', '', src, flags=re.S)
        out = translate(bare, table, missing)
        out = scripts(out, table, missing)
        out = relink(out)
        out = out.replace('<html lang="en-GB">', '<html lang="cy">', 1)
        out = re.sub(r'<meta property="og:locale" content="en_GB">\n?', '', out, count=1)
        out = out.replace('</head>', '<meta property="og:locale" content="cy">\n</head>', 1)
        out = inject_head(out, alternates(name))
        out = switcher(out, path_for(name), 'English', 'en-GB')
        open(os.path.join(OUT, name), 'w', encoding='utf-8').write(out)
        long_meta.extend(audit(name, out))
        broken.extend(check_scripts(name, out))

    n = sitemap()
    print(f'sitemap: {n} urls', file=sys.stderr)
    done = sum(1 for _ in table)
    print(f'built {len(L.pages())} Welsh pages, {done} strings translated, '
          f'{len(missing)} still English', file=sys.stderr)
    for line in broken:
        print('  BROKEN: ' + line, file=sys.stderr)
    for line in long_meta:
        print('  over length: ' + line, file=sys.stderr)
    if missing:
        json.dump(sorted(missing), open(os.path.join(L.ROOT, 'i18n', 'cy.todo.json'),
                                        'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(build())
