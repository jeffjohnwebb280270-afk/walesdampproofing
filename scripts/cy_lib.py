#!/usr/bin/env python3
"""Shared machinery for the Welsh build.

Translating text node by node does not work: inline tags such as <b> and <a>
split a sentence into fragments, and Welsh does not keep English word order, so
the fragments cannot be swapped back one for one. Instead this module finds
"leaf blocks" — elements whose children are only text and inline markup — and
treats the whole inner HTML of each as a single translatable unit.
"""
import json, os, re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tags that flow inside a sentence. Anything else starts a new block.
INLINE = {
    'a', 'abbr', 'b', 'br', 'cite', 'code', 'del', 'em', 'i', 'ins', 'kbd',
    'mark', 'q', 's', 'samp', 'small', 'span', 'strong', 'sub', 'sup', 'time',
    'u', 'var', 'wbr', 'img',
}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
OPAQUE = {'script', 'style', 'svg'}

TEXT_ATTRS = {'alt', 'title', 'aria-label', 'placeholder'}
META_KEYS = {
    'description', 'twitter:title', 'twitter:description',
    'og:title', 'og:description', 'og:image:alt', 'og:site_name',
}


SVG_RE = re.compile(r'<svg\b[^>]*>.*?</svg>', re.S | re.I)


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def mask(span):
    """Swap SVG subtrees for placeholders, so keys stay readable prose."""
    kept = []

    def take(m):
        kept.append(m.group(0))
        return f'\u27e6{len(kept) - 1}\u27e7'

    return norm(SVG_RE.sub(take, span)), kept


def unmask(text, kept):
    return re.sub(r'\u27e6(\d+)\u27e7', lambda m: kept[int(m.group(1))], text)


def translatable(s):
    """Does this string contain anything a translator would act on?"""
    if not s:
        return False
    bare = re.sub(r'<[^>]*>', '', s)
    bare = re.sub(r'&[a-zA-Z]+;|&#\d+;', '', bare)
    if not re.search(r'[A-Za-z]{2}', bare):
        return False
    # A bare email address, phone number or URL is the same in both languages.
    if re.fullmatch(r'[\w.+-]+@[\w.-]+|https?://\S+|\+?[\d\s()-]{7,}', bare.strip()):
        return False
    return True


class Segmenter(HTMLParser):
    """Collect leaf-block inner HTML spans plus translatable attribute values."""

    def __init__(self, html):
        super().__init__(convert_charrefs=False)
        self.html = html
        starts, pos = [0], 0
        for line in html.splitlines(keepends=True):
            pos += len(line)
            starts.append(pos)
        self._line_starts = starts
        self.stack = []          # [tag, content_start, has_block_child]
        self.blocks = []         # (start, end) source spans
        self.attrs = []          # (start, end) spans of attribute values
        self.opaque = 0
        self.feed(html)

    def _off(self):
        line, col = self.getpos()
        return self._line_starts[line - 1] + col

    def _attr_spans(self, tag, attrs, tag_start):
        raw = self.get_starttag_text() or ''
        a = dict(attrs)
        wanted = []
        for k, v in attrs:
            if k in TEXT_ATTRS and translatable(v or ''):
                wanted.append((k, v))
        if tag == 'meta':
            key = a.get('name') or a.get('property')
            if key in META_KEYS and translatable(a.get('content', '')):
                wanted.append(('content', a['content']))
        for k, v in wanted:
            # Locate the value inside the raw tag text so the span is exact.
            m = re.search(re.escape(k) + r'\s*=\s*(["\'])(.*?)\1', raw, re.S | re.I)
            if m and m.group(2) == v:
                self.attrs.append((tag_start + m.start(2), tag_start + m.end(2)))

    def handle_starttag(self, tag, attrs):
        start = self._off()
        if self.opaque:
            if tag in OPAQUE:
                self.opaque += 1
            return
        self._attr_spans(tag, attrs, start)
        if tag in OPAQUE:
            self.opaque = 1
            return
        if tag in VOID:
            return
        self.stack.append([tag, start + len(self.get_starttag_text() or ''), False])

    def handle_startendtag(self, tag, attrs):
        if not self.opaque:
            self._attr_spans(tag, attrs, self._off())

    def handle_endtag(self, tag):
        if self.opaque:
            if tag in OPAQUE:
                self.opaque -= 1
            return
        end = self._off()
        # Tolerate unclosed tags by unwinding to the matching name.
        while self.stack:
            name, content_start, has_block = self.stack.pop()
            if name != tag:
                continue
            emitted = False
            if not has_block:
                span = self.html[content_start:end]
                if translatable(span):
                    self.blocks.append((content_start, end))
                    emitted = True
            if self.stack and (tag not in INLINE or emitted or has_block):
                self.stack[-1][2] = True
            return


def segments(html):
    """All translatable source spans in a page, ordered and non-overlapping."""
    s = Segmenter(html)
    spans = sorted(set(s.blocks + s.attrs))
    out, last = [], -1
    for a, b in spans:
        if a >= last:
            out.append((a, b))
            last = b
    return out


def jsonld_spans(html):
    """Prose fields inside JSON-LD, as (start, end) spans of the JSON string."""
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         html, re.S):
        body, base = m.group(1), m.start(1)
        for f in re.finditer(
                r'"(name|description|alternateName)"\s*:\s*"((?:[^"\\]|\\.)*)"', body):
            val = json.loads('"' + f.group(2) + '"')
            if translatable(val) and len(val.split()) > 1:
                out.append((base + f.start(2), base + f.end(2), val))
    return out


def load(name):
    path = os.path.join(ROOT, 'i18n', name)
    if os.path.exists(path):
        return json.load(open(path, encoding='utf-8'))
    return {}


def pages():
    return sorted(f for f in os.listdir(ROOT) if f.endswith('.html'))
